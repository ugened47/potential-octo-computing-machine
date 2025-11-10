"""Video metadata extraction service."""

import os
import tempfile
from collections.abc import Callable
from uuid import UUID

import av
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.config import settings
from app.models.video import Video, VideoStatus
from app.services.s3 import S3Service


class VideoMetadataService:
    """Service for extracting video metadata."""

    def __init__(self, db: AsyncSession):
        """Initialize metadata service.

        Args:
            db: Database session
        """
        self.db = db
        self.s3_service = S3Service()

    def extract_metadata(self, video_path: str) -> dict[str, str | float | None]:
        """Extract metadata from video file using PyAV.

        Args:
            video_path: Path to video file

        Returns:
            Dictionary with duration, resolution, and format

        Raises:
            ValueError: If video file cannot be opened or has no video stream
        """
        try:
            container = av.open(video_path)

            # Find video stream
            video_stream = None
            for stream in container.streams.video:
                video_stream = stream
                break

            if not video_stream:
                raise ValueError("No video stream found in file")

            # Get duration (in seconds)
            duration = None
            if container.duration is not None:
                # PyAV duration is in microseconds, convert to seconds
                duration = float(container.duration) / 1000000.0
            elif video_stream.duration is not None and video_stream.time_base:
                # Fallback to stream duration
                duration = float(video_stream.duration * video_stream.time_base)

            # Get resolution
            resolution = None
            if video_stream.width and video_stream.height:
                resolution = f"{video_stream.width}x{video_stream.height}"

            # Get format (codec name)
            format_name = None
            if video_stream.codec:
                format_name = video_stream.codec.name

            # Also try to get container format
            container_format = container.format.name if container.format else None

            container.close()

            return {
                "duration": duration,
                "resolution": resolution,
                "format": format_name or container_format,
            }

        except Exception as e:
            raise ValueError(f"Failed to extract metadata: {str(e)}") from e

    def generate_thumbnail(
        self, video_path: str, output_path: str, time_offset: float = 1.0
    ) -> None:
        """Generate thumbnail from video at specified time offset.

        Args:
            video_path: Path to video file
            output_path: Path to save thumbnail image
            time_offset: Time offset in seconds (default: 1.0 to skip potential black frames)

        Raises:
            ValueError: If thumbnail generation fails
        """
        try:
            container = av.open(video_path)

            # Find video stream
            video_stream = None
            for stream in container.streams.video:
                video_stream = stream
                break

            if not video_stream:
                raise ValueError("No video stream found in file")

            # Seek to specified time
            # PyAV uses microseconds for timestamps
            seek_time = int(time_offset * 1000000)
            container.seek(seek_time, stream=video_stream)

            # Decode frames until we get a keyframe
            frame = None
            for packet in container.demux(video_stream):
                for decoded_frame in packet.decode():
                    if decoded_frame:
                        frame = decoded_frame
                        break
                if frame:
                    break

            if not frame:
                # Fallback: seek to start and get first frame
                container.seek(0, stream=video_stream)
                for packet in container.demux(video_stream):
                    for decoded_frame in packet.decode():
                        if decoded_frame:
                            frame = decoded_frame
                            break
                    if frame:
                        break

            if not frame:
                raise ValueError("Could not extract frame from video")

            # Resize frame to max 1280x720 for thumbnail
            frame_width = frame.width
            frame_height = frame.height
            max_width = 1280
            max_height = 720

            if frame_width > max_width or frame_height > max_height:
                scale = min(max_width / frame_width, max_height / frame_height)
                new_width = int(frame_width * scale)
                new_height = int(frame_height * scale)
                frame = frame.reformat(width=new_width, height=new_height)

            # Convert to RGB and save as JPEG
            frame_rgb = frame.to_ndarray(format="rgb24")

            from PIL import Image

            img = Image.fromarray(frame_rgb)
            img.save(output_path, "JPEG", quality=85)

            container.close()

        except Exception as e:
            raise ValueError(f"Failed to generate thumbnail: {str(e)}") from e

    def download_video_from_s3(self, s3_key: str, local_path: str) -> None:
        """Download video file from S3.

        Args:
            s3_key: S3 object key
            local_path: Local path to save the file
        """
        import boto3
        from botocore.exceptions import ClientError

        client_kwargs = {
            "service_name": "s3",
            "aws_access_key_id": settings.aws_access_key_id,
            "aws_secret_access_key": settings.aws_secret_access_key,
            "region_name": settings.aws_region,
        }

        endpoint_url = settings.s3_endpoint_url
        if endpoint_url:
            client_kwargs["endpoint_url"] = endpoint_url

        s3_client = boto3.client(**client_kwargs)

        try:
            s3_client.download_file(settings.s3_bucket, s3_key, local_path)
        except ClientError as e:
            raise ValueError(f"Failed to download video from S3: {str(e)}") from e

    async def extract_video_metadata(
        self, video_id: UUID, update_progress: Callable[[int], None] | None = None
    ) -> Video:
        """Extract metadata for a video (full workflow).

        Args:
            video_id: Video ID
            update_progress: Optional callback to update progress (progress: int)

        Returns:
            Updated video record
        """
        # Get video
        result = await self.db.execute(select(Video).where(Video.id == video_id))
        video = result.scalar_one_or_none()

        if not video:
            raise ValueError(f"Video {video_id} not found")

        if not video.s3_key:
            raise ValueError(f"Video {video_id} has no S3 key")

        # Update progress: Downloading
        if update_progress:
            update_progress(10)

        # Download video from S3
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as video_file:
            video_path = video_file.name

        try:
            self.download_video_from_s3(video.s3_key, video_path)

            # Update progress: Extracting metadata
            if update_progress:
                update_progress(50)

            # Extract metadata
            metadata = self.extract_metadata(video_path)

            # Update progress: Generating thumbnail
            if update_progress:
                update_progress(70)

            # Generate thumbnail
            thumbnail_path = None
            thumbnail_s3_key = None
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as thumb_file:
                    thumbnail_path = thumb_file.name

                # Generate thumbnail at 1 second (skip potential black frames)
                self.generate_thumbnail(video_path, thumbnail_path, time_offset=1.0)

                # Upload thumbnail to S3
                thumbnail_s3_key = self.s3_service.upload_thumbnail(
                    video.user_id, video.id, thumbnail_path
                )

                # Get thumbnail URL
                thumbnail_url = self.s3_service.get_thumbnail_url(thumbnail_s3_key)
            except Exception as e:
                # Log error but don't fail the whole process
                print(f"Warning: Failed to generate thumbnail: {str(e)}")
                thumbnail_url = None

            # Update progress: Saving
            if update_progress:
                update_progress(90)

            # Update video record
            video.duration = metadata["duration"]
            video.resolution = metadata["resolution"]
            if metadata["format"]:
                video.format = metadata["format"]
            video.thumbnail_url = thumbnail_url
            video.status = VideoStatus.COMPLETED

            await self.db.commit()
            await self.db.refresh(video)

            # Clean up thumbnail file
            if thumbnail_path and os.path.exists(thumbnail_path):
                os.unlink(thumbnail_path)

            # Update progress: Complete
            if update_progress:
                update_progress(100)

            return video

        finally:
            # Clean up video file
            if os.path.exists(video_path):
                os.unlink(video_path)
