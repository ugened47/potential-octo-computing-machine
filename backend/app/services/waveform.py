"""Waveform generation service for audio visualization."""

import json
import os
import tempfile
from typing import Callable, Optional
from uuid import UUID

import av
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.config import settings
from app.models.video import Video
from app.services.s3 import S3Service


class WaveformService:
    """Service for generating waveform data from video audio."""

    def __init__(self, db: AsyncSession):
        """Initialize waveform service.

        Args:
            db: Database session
        """
        self.db = db
        self.s3_service = S3Service()

    def extract_audio(self, video_path: str, audio_path: str) -> None:
        """Extract audio track from video file.

        Args:
            video_path: Path to video file
            audio_path: Path to save extracted audio file

        Raises:
            ValueError: If audio extraction fails
        """
        try:
            container = av.open(video_path)

            # Find audio stream
            audio_stream = None
            for stream in container.streams.audio:
                audio_stream = stream
                break

            if not audio_stream:
                raise ValueError("No audio stream found in video")

            # Extract audio to WAV file
            output_container = av.open(audio_path, mode="w")
            sample_rate = audio_stream.rate or 44100
            output_stream = output_container.add_stream("pcm_s16le", rate=sample_rate)

            for packet in container.demux(audio_stream):
                for frame in packet.decode():
                    if frame:
                        # Resample if needed
                        frame_rate = getattr(frame, 'rate', sample_rate)
                        if frame_rate != sample_rate:
                            frame.pts = None
                            resampled = frame.resample(sample_rate)
                            for resampled_packet in output_stream.encode(resampled):
                                output_container.mux(resampled_packet)
                        else:
                            for encoded_packet in output_stream.encode(frame):
                                output_container.mux(encoded_packet)

            # Flush remaining packets
            for encoded_packet in output_stream.encode():
                output_container.mux(encoded_packet)

            output_container.close()
            container.close()

        except Exception as e:
            raise ValueError(f"Failed to extract audio: {str(e)}") from e

    def generate_waveform_peaks(
        self, audio_path: str, samples: int = 2000
    ) -> list[float]:
        """Generate waveform peaks data from audio file.

        Args:
            audio_path: Path to audio file
            samples: Number of samples to generate (default: 2000)

        Returns:
            List of normalized peak values (0.0 to 1.0)

        Raises:
            ValueError: If waveform generation fails
        """
        try:
            container = av.open(audio_path)

            # Find audio stream
            audio_stream = None
            for stream in container.streams.audio:
                audio_stream = stream
                break

            if not audio_stream:
                raise ValueError("No audio stream found")

            # Read all audio frames
            audio_data = []
            for packet in container.demux(audio_stream):
                for frame in packet.decode():
                    if frame:
                        # Convert to numpy array
                        array = frame.to_ndarray()
                        # Handle multi-channel audio (take first channel or average)
                        if len(array.shape) > 1:
                            array = np.mean(array, axis=0)
                        audio_data.append(array)

            container.close()

            if not audio_data:
                raise ValueError("No audio data found")

            # Concatenate all audio data
            full_audio = np.concatenate(audio_data)

            # Calculate RMS (Root Mean Square) for each sample window
            total_samples = len(full_audio)
            window_size = max(1, total_samples // samples)
            peaks = []

            for i in range(0, total_samples, window_size):
                window = full_audio[i : i + window_size]
                if len(window) > 0:
                    # Calculate RMS
                    rms = np.sqrt(np.mean(window**2))
                    peaks.append(float(rms))

            # Normalize peaks to 0.0-1.0 range
            if peaks:
                max_peak = max(peaks)
                if max_peak > 0:
                    peaks = [p / max_peak for p in peaks]
                else:
                    peaks = [0.0] * len(peaks)

            return peaks

        except Exception as e:
            raise ValueError(f"Failed to generate waveform: {str(e)}") from e

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

    def upload_waveform_data(
        self, user_id: UUID, video_id: UUID, peaks: list[float], duration: float
    ) -> str:
        """Upload waveform data to S3 as JSON.

        Args:
            user_id: User ID
            video_id: Video ID
            peaks: Waveform peaks data
            duration: Video duration in seconds

        Returns:
            S3 key of uploaded waveform data
        """
        import boto3
        from botocore.exceptions import ClientError
        from io import BytesIO

        waveform_data = {
            "peaks": peaks,
            "duration": duration,
            "sample_rate": 44100,  # Standard sample rate
        }

        s3_key = f"waveforms/{user_id}/{video_id}/waveform.json"

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
            json_data = json.dumps(waveform_data)
            json_bytes = BytesIO(json_data.encode("utf-8"))
            s3_client.upload_fileobj(
                json_bytes,
                settings.s3_bucket,
                s3_key,
                ExtraArgs={"ContentType": "application/json"},
            )
            return s3_key
        except ClientError as e:
            raise ValueError(f"Failed to upload waveform data: {str(e)}") from e

    def get_waveform_data(self, s3_key: str) -> dict:
        """Get waveform data from S3.

        Args:
            s3_key: S3 key of waveform data

        Returns:
            Dictionary with peaks, duration, and sample_rate

        Raises:
            ValueError: If retrieval fails
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
            response = s3_client.get_object(Bucket=settings.s3_bucket, Key=s3_key)
            data = json.loads(response["Body"].read().decode("utf-8"))
            return data
        except ClientError as e:
            raise ValueError(f"Failed to get waveform data: {str(e)}") from e

    async def generate_waveform(
        self,
        video_id: UUID,
        update_progress: Optional[Callable[[int], None]] = None,
    ) -> dict:
        """Generate waveform data for a video (full workflow).

        Args:
            video_id: Video ID
            update_progress: Optional callback to update progress (progress: int)

        Returns:
            Dictionary with peaks, duration, and sample_rate

        Raises:
            ValueError: If generation fails
        """
        # Get video
        result = await self.db.execute(select(Video).where(Video.id == video_id))
        video = result.scalar_one_or_none()

        if not video:
            raise ValueError(f"Video {video_id} not found")

        if not video.s3_key:
            raise ValueError(f"Video {video_id} has no S3 key")

        if not video.duration:
            raise ValueError(f"Video {video_id} has no duration")

        # Check if waveform already exists
        waveform_s3_key = f"waveforms/{video.user_id}/{video_id}/waveform.json"
        try:
            waveform_data = self.get_waveform_data(waveform_s3_key)
            if waveform_data:
                return waveform_data
        except ValueError:
            # Waveform doesn't exist, generate it
            pass

        # Update progress: Downloading
        if update_progress:
            update_progress(10)

        # Download video from S3
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as video_file:
            video_path = video_file.name

        audio_path = None
        try:
            self.download_video_from_s3(video.s3_key, video_path)

            # Update progress: Extracting audio
            if update_progress:
                update_progress(30)

            # Extract audio
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as audio_file:
                audio_path = audio_file.name

            self.extract_audio(video_path, audio_path)

            # Update progress: Generating waveform
            if update_progress:
                update_progress(60)

            # Generate waveform peaks
            peaks = self.generate_waveform_peaks(audio_path, samples=2000)

            # Update progress: Uploading
            if update_progress:
                update_progress(80)

            # Upload waveform data to S3
            waveform_s3_key = self.upload_waveform_data(
                video.user_id, video_id, peaks, video.duration
            )

            # Update progress: Complete
            if update_progress:
                update_progress(100)

            return {
                "peaks": peaks,
                "duration": video.duration,
                "sample_rate": 44100,
            }

        finally:
            # Clean up files
            if os.path.exists(video_path):
                os.unlink(video_path)
            if audio_path and os.path.exists(audio_path):
                os.unlink(audio_path)

