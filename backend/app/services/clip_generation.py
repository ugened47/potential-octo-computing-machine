"""Clip generation service for creating video clips."""

import os
import tempfile
from typing import Callable, Optional
from uuid import UUID

import av
import boto3
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.config import settings
from app.models.clip import Clip, ClipStatus
from app.models.video import Video


class ClipGenerationService:
    """Service for generating video clips."""

    def __init__(self, db: AsyncSession):
        """Initialize clip generation service.

        Args:
            db: Database session
        """
        self.db = db
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.aws_region,
            endpoint_url=settings.s3_endpoint_url,
        )

    def download_video_from_s3(self, s3_key: str, local_path: str) -> None:
        """Download video file from S3.

        Args:
            s3_key: S3 object key
            local_path: Local path to save the file
        """
        self.s3_client.download_file(settings.s3_bucket, s3_key, local_path)

    def extract_clip(
        self,
        video_path: str,
        output_path: str,
        start_time: float,
        end_time: float,
    ) -> None:
        """Extract a clip from video file.

        Args:
            video_path: Path to input video file
            output_path: Path to save extracted clip
            start_time: Start time in seconds
            end_time: End time in seconds
        """
        input_container = av.open(video_path)
        output_container = av.open(output_path, mode="w")

        # Find video and audio streams
        video_stream = None
        audio_stream = None

        for stream in input_container.streams.video:
            video_stream = stream
            break
        for stream in input_container.streams.audio:
            audio_stream = stream
            break

        if not video_stream:
            raise ValueError("No video stream found")

        # Copy streams to output
        video_out = output_container.add_stream(template=video_stream)
        audio_out = (
            output_container.add_stream(template=audio_stream)
            if audio_stream
            else None
        )

        # Seek to start time
        input_container.seek(int(start_time * av.time_base))

        # Process frames
        for packet in input_container.demux(video_stream):
            if packet.pts is None:
                continue

            packet_time = packet.pts * packet.time_base
            if packet_time < start_time:
                continue
            if packet_time >= end_time:
                break

            packet.stream = video_out
            output_container.mux(packet)

        # Process audio if available
        if audio_out:
            input_container.seek(int(start_time * av.time_base))
            for packet in input_container.demux(audio_stream):
                if packet.pts is None:
                    continue

                packet_time = packet.pts * packet.time_base
                if packet_time < start_time:
                    continue
                if packet_time >= end_time:
                    break

                packet.stream = audio_out
                output_container.mux(packet)

        # Flush streams
        for packet in video_out.encode():
            output_container.mux(packet)
        if audio_out:
            for packet in audio_out.encode():
                output_container.mux(packet)

        output_container.close()
        input_container.close()

    async def generate_clip(
        self,
        clip_id: UUID,
        update_progress: Optional[Callable[[int], None]] = None,
    ) -> Clip:
        """Generate a video clip.

        Args:
            clip_id: Clip ID
            update_progress: Optional callback to update progress

        Returns:
            Updated clip record
        """
        # Get clip
        result = await self.db.execute(select(Clip).where(Clip.id == clip_id))
        clip = result.scalar_one_or_none()

        if not clip:
            raise ValueError(f"Clip {clip_id} not found")

        # Get video
        result = await self.db.execute(select(Video).where(Video.id == clip.video_id))
        video = result.scalar_one_or_none()

        if not video:
            raise ValueError(f"Video {clip.video_id} not found")

        if not video.s3_key:
            raise ValueError(f"Video {clip.video_id} has no S3 key")

        # Update progress: Downloading
        if update_progress:
            update_progress(10)

        # Download video
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as video_file:
            video_path = video_file.name

        try:
            self.download_video_from_s3(video.s3_key, video_path)

            # Update progress: Extracting clip
            if update_progress:
                update_progress(50)

            # Extract clip
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as clip_file:
                clip_path = clip_file.name

            try:
                self.extract_clip(
                    video_path, clip_path, clip.start_time, clip.end_time
                )

                # Update progress: Uploading
                if update_progress:
                    update_progress(80)

                # Upload clip to S3
                clip_s3_key = f"clips/{video.user_id}/{clip.video_id}/{clip.id}.mp4"
                self.s3_client.upload_file(
                    clip_path,
                    settings.s3_bucket,
                    clip_s3_key,
                    ExtraArgs={"ContentType": "video/mp4"},
                )

                # Get clip URL (presigned URL for now)
                clip_url = self.s3_client.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": settings.s3_bucket, "Key": clip_s3_key},
                    ExpiresIn=3600 * 24 * 7,  # 7 days
                )

                # Update clip record
                clip.clip_url = clip_s3_key
                clip.status = ClipStatus.COMPLETED

                # Calculate duration
                clip.duration = clip.end_time - clip.start_time

                await self.db.commit()
                await self.db.refresh(clip)

                # Update progress: Complete
                if update_progress:
                    update_progress(100)

                return clip

            finally:
                if os.path.exists(clip_path):
                    os.unlink(clip_path)

        finally:
            if os.path.exists(video_path):
                os.unlink(video_path)

