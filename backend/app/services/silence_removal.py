"""Silence removal service for video processing."""

import os
import tempfile
from typing import Any, Callable, Optional
from uuid import UUID

import av
import boto3
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.config import settings
from app.models.video import Video, VideoStatus
from app.services.s3 import S3Service


class SilenceRemovalService:
    """Service for detecting and removing silent segments from videos."""

    def __init__(self, db: AsyncSession):
        """Initialize silence removal service.

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
        self.s3_service = S3Service()

    def download_video_from_s3(self, s3_key: str, local_path: str) -> None:
        """Download video file from S3.

        Args:
            s3_key: S3 object key
            local_path: Local path to save the file
        """
        self.s3_client.download_file(settings.s3_bucket, s3_key, local_path)

    def extract_audio_from_video(self, video_path: str, output_path: str) -> None:
        """Extract audio track from video file.

        Args:
            video_path: Path to video file
            output_path: Path to save extracted audio file
        """
        container = av.open(video_path)
        audio_stream = None

        # Find audio stream
        for stream in container.streams.audio:
            audio_stream = stream
            break

        if not audio_stream:
            raise ValueError("No audio stream found in video")

        # Extract audio
        output_container = av.open(output_path, mode="w")
        output_stream = output_container.add_stream("pcm_s16le", rate=16000)

        for frame in container.decode(audio_stream):
            frame.pts = None
            for packet in output_stream.encode(frame):
                output_container.mux(packet)

        # Flush remaining packets
        for packet in output_stream.encode():
            output_container.mux(packet)

        output_container.close()
        container.close()

    def detect_silence_segments(
        self,
        audio_path: str,
        threshold_db: int = -40,
        min_duration_ms: int = 1000,
    ) -> list[dict[str, Any]]:
        """Detect silent segments in audio file.

        Args:
            audio_path: Path to audio file
            threshold_db: Silence threshold in dB (default: -40)
            min_duration_ms: Minimum silence duration in milliseconds (default: 1000)

        Returns:
            List of silent segments with start_time, end_time, and duration
        """
        container = av.open(audio_path)
        audio_stream = None

        # Find audio stream
        for stream in container.streams.audio:
            audio_stream = stream
            break

        if not audio_stream:
            raise ValueError("No audio stream found in audio file")

        # Convert threshold from dB to linear scale
        threshold_linear = 10 ** (threshold_db / 20.0)

        # Read audio samples
        samples = []
        timestamps = []

        for frame in container.decode(audio_stream):
            # Convert to numpy array
            array = frame.to_ndarray()
            if len(array.shape) > 1:
                # Convert to mono if stereo
                array = np.mean(array, axis=0)

            # Calculate RMS (Root Mean Square) energy
            rms = np.sqrt(np.mean(array**2))

            samples.append(rms)
            timestamps.append(frame.time)

        container.close()

        if not samples:
            return []

        # Detect silence segments
        silent_segments = []
        in_silence = False
        silence_start = None

        min_duration_seconds = min_duration_ms / 1000.0

        for i, (rms, timestamp) in enumerate(zip(samples, timestamps)):
            is_silent = rms < threshold_linear

            if is_silent and not in_silence:
                # Start of silence
                in_silence = True
                silence_start = timestamp
            elif not is_silent and in_silence:
                # End of silence
                duration = timestamp - silence_start
                if duration >= min_duration_seconds:
                    silent_segments.append(
                        {
                            "start_time": silence_start,
                            "end_time": timestamp,
                            "duration": duration,
                        }
                    )
                in_silence = False
                silence_start = None

        # Handle silence that extends to end of audio
        if in_silence and silence_start is not None:
            duration = timestamps[-1] - silence_start
            if duration >= min_duration_seconds:
                silent_segments.append(
                    {
                        "start_time": silence_start,
                        "end_time": timestamps[-1],
                        "duration": duration,
                    }
                )

        return silent_segments

    def remove_silence_from_video(
        self,
        video_path: str,
        output_path: str,
        silent_segments: list[dict[str, Any]],
        excluded_segments: Optional[list[int]] = None,
    ) -> None:
        """Remove silent segments from video using FFmpeg.

        Args:
            video_path: Path to input video file
            output_path: Path to save processed video
            silent_segments: List of silent segments to remove
            excluded_segments: Optional list of segment indices to exclude from removal
        """
        if excluded_segments is None:
            excluded_segments = []

        # Filter out excluded segments
        segments_to_remove = [
            seg
            for i, seg in enumerate(silent_segments)
            if i not in excluded_segments
        ]

        if not segments_to_remove:
            # No segments to remove, just copy the video
            import shutil

            shutil.copy2(video_path, output_path)
            return

        # Build FFmpeg filter complex to remove segments
        # We'll use the concat demuxer approach: split video into segments and concatenate non-silent parts
        container = av.open(video_path)
        video_stream = None
        audio_stream = None

        for stream in container.streams.video:
            video_stream = stream
            break
        for stream in container.streams.audio:
            audio_stream = stream
            break

        if not video_stream:
            raise ValueError("No video stream found")

        container.close()

        # Get video duration
        container = av.open(video_path)
        duration = container.duration / av.time_base if container.duration else None
        container.close()

        # Build list of segments to keep (inverse of segments to remove)
        segments_to_keep = []
        current_start = 0.0

        for seg in sorted(segments_to_remove, key=lambda x: x["start_time"]):
            if current_start < seg["start_time"]:
                segments_to_keep.append(
                    {"start": current_start, "end": seg["start_time"]}
                )
            current_start = max(current_start, seg["end_time"])

        # Add final segment if there's remaining video
        if duration and current_start < duration:
            segments_to_keep.append({"start": current_start, "end": duration})

        if not segments_to_keep:
            raise ValueError("No segments to keep after silence removal")

        # Use PyAV to extract and concatenate segments
        input_container = av.open(video_path)
        output_container = av.open(output_path, mode="w")

        # Copy streams
        video_out = output_container.add_stream(
            template=video_stream
        ) if video_stream else None
        audio_out = (
            output_container.add_stream(template=audio_stream)
            if audio_stream
            else None
        )

        # Process each segment
        for seg in segments_to_keep:
            # Seek to start time
            input_container.seek(int(seg["start"] * av.time_base))

            # Decode and encode frames in this segment
            for packet in input_container.demux(video_stream):
                if packet.pts is None:
                    continue

                packet_time = packet.pts * packet.time_base
                if packet_time < seg["start"]:
                    continue
                if packet_time >= seg["end"]:
                    break

                if video_out:
                    packet.stream = video_out
                    output_container.mux(packet)

            if audio_out:
                input_container.seek(int(seg["start"] * av.time_base))
                for packet in input_container.demux(audio_stream):
                    if packet.pts is None:
                        continue

                    packet_time = packet.pts * packet.time_base
                    if packet_time < seg["start"]:
                        continue
                    if packet_time >= seg["end"]:
                        break

                    packet.stream = audio_out
                    output_container.mux(packet)

        # Flush streams
        if video_out:
            for packet in video_out.encode():
                output_container.mux(packet)
        if audio_out:
            for packet in audio_out.encode():
                output_container.mux(packet)

        output_container.close()
        input_container.close()

    async def detect_silence(
        self,
        video_id: UUID,
        threshold_db: int = -40,
        min_duration_ms: int = 1000,
    ) -> list[dict[str, Any]]:
        """Detect silent segments in a video (preview only, doesn't modify video).

        Args:
            video_id: Video ID
            threshold_db: Silence threshold in dB
            min_duration_ms: Minimum silence duration in milliseconds

        Returns:
            List of silent segments
        """
        # Get video
        result = await self.db.execute(select(Video).where(Video.id == video_id))
        video = result.scalar_one_or_none()

        if not video:
            raise ValueError(f"Video {video_id} not found")

        if not video.s3_key:
            raise ValueError(f"Video {video_id} has no S3 key")

        # Download video
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as video_file:
            video_path = video_file.name

        try:
            self.download_video_from_s3(video.s3_key, video_path)

            # Extract audio
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as audio_file:
                audio_path = audio_file.name

            try:
                self.extract_audio_from_video(video_path, audio_path)

                # Detect silence
                segments = self.detect_silence_segments(
                    audio_path, threshold_db, min_duration_ms
                )

                return segments

            finally:
                if os.path.exists(audio_path):
                    os.unlink(audio_path)

        finally:
            if os.path.exists(video_path):
                os.unlink(video_path)

    async def remove_silence(
        self,
        video_id: UUID,
        threshold_db: int = -40,
        min_duration_ms: int = 1000,
        excluded_segments: Optional[list[int]] = None,
        update_progress: Optional[Callable[[int], None]] = None,
    ) -> Video:
        """Remove silent segments from a video.

        Args:
            video_id: Video ID
            threshold_db: Silence threshold in dB
            min_duration_ms: Minimum silence duration in milliseconds
            excluded_segments: Optional list of segment indices to exclude
            update_progress: Optional callback to update progress

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

        # Download video
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as video_file:
            video_path = video_file.name

        try:
            self.download_video_from_s3(video.s3_key, video_path)

            # Update progress: Detecting silence
            if update_progress:
                update_progress(20)

            # Extract audio and detect silence
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as audio_file:
                audio_path = audio_file.name

            try:
                self.extract_audio_from_video(video_path, audio_path)
                silent_segments = self.detect_silence_segments(
                    audio_path, threshold_db, min_duration_ms
                )

                # Update progress: Removing silence
                if update_progress:
                    update_progress(40)

                # Remove silence from video
                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=".mp4"
                ) as output_file:
                    output_path = output_file.name

                try:
                    self.remove_silence_from_video(
                        video_path, output_path, silent_segments, excluded_segments
                    )

                    # Update progress: Uploading
                    if update_progress:
                        update_progress(80)

                    # Store original video S3 key for undo capability
                    original_s3_key = video.s3_key
                    original_s3_key_backup = f"originals/{video.user_id}/{video.id}/{os.path.basename(original_s3_key)}"

                    # Upload original to backup location if not already there
                    try:
                        self.s3_client.head_object(
                            Bucket=settings.s3_bucket, Key=original_s3_key_backup
                        )
                    except self.s3_client.exceptions.ClientError:
                        # Original backup doesn't exist, copy it
                        copy_source = {
                            "Bucket": settings.s3_bucket,
                            "Key": original_s3_key,
                        }
                        self.s3_client.copy_object(
                            CopySource=copy_source,
                            Bucket=settings.s3_bucket,
                            Key=original_s3_key_backup,
                        )

                    # Upload processed video
                    new_s3_key = f"videos/{video.user_id}/{video.id}/processed_{os.path.basename(original_s3_key)}"
                    self.s3_client.upload_file(
                        output_path,
                        settings.s3_bucket,
                        new_s3_key,
                        ExtraArgs={"ContentType": "video/mp4"},
                    )

                    # Update video record
                    video.s3_key = new_s3_key
                    video.status = VideoStatus.COMPLETED

                    # Update duration if available
                    container = av.open(output_path)
                    if container.duration:
                        video.duration = container.duration / av.time_base
                    container.close()

                    await self.db.commit()
                    await self.db.refresh(video)

                    # Update progress: Complete
                    if update_progress:
                        update_progress(100)

                    return video

                finally:
                    if os.path.exists(output_path):
                        os.unlink(output_path)

            finally:
                if os.path.exists(audio_path):
                    os.unlink(audio_path)

        finally:
            if os.path.exists(video_path):
                os.unlink(video_path)

