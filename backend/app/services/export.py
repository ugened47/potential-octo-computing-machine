"""Export service for video processing and export operations."""

import asyncio
import os
import subprocess
import tempfile
import zipfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import UUID

import av
import boto3
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.config import settings
from app.models import (
    Export,
    ExportStatus,
    ExportType,
    Format,
    QualityPreset,
    Resolution,
    Video,
)
from app.services.s3 import S3Service


@dataclass
class QualitySettings:
    """Quality settings for video export."""

    crf: int
    bitrate: str
    preset: str


@dataclass
class ResolutionSettings:
    """Resolution settings for video export."""

    width: int
    height: int


class ExportService:
    """Service for video export operations using FFmpeg."""

    # Quality presets mapping
    QUALITY_PRESETS: dict[QualityPreset, QualitySettings] = {
        QualityPreset.HIGH: QualitySettings(crf=18, bitrate="8M", preset="slow"),
        QualityPreset.MEDIUM: QualitySettings(crf=23, bitrate="4M", preset="medium"),
        QualityPreset.LOW: QualitySettings(crf=28, bitrate="2M", preset="fast"),
    }

    # Resolution mappings
    RESOLUTIONS: dict[Resolution, ResolutionSettings] = {
        Resolution.R_720P: ResolutionSettings(width=1280, height=720),
        Resolution.R_1080P: ResolutionSettings(width=1920, height=1080),
        Resolution.R_4K: ResolutionSettings(width=3840, height=2160),
    }

    # Format encoder mappings
    FORMAT_ENCODERS: dict[Format, dict[str, str]] = {
        Format.MP4: {
            "video_codec": "libx264",
            "audio_codec": "aac",
            "container": "mp4",
        },
        Format.MOV: {
            "video_codec": "libx264",
            "audio_codec": "aac",
            "container": "mov",
        },
        Format.WEBM: {
            "video_codec": "libvpx-vp9",
            "audio_codec": "libopus",
            "container": "webm",
        },
    }

    def __init__(self, db: AsyncSession):
        """Initialize export service.

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

    async def download_video_from_s3(self, s3_key: str, local_path: str) -> None:
        """Download video file from S3.

        Args:
            s3_key: S3 object key
            local_path: Local path to save the file
        """
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: self.s3_client.download_file(
                settings.s3_bucket, s3_key, local_path
            ),
        )

    async def upload_to_s3(
        self, local_path: str, s3_key: str
    ) -> tuple[str, int]:
        """Upload file to S3 and return CloudFront URL and file size.

        Args:
            local_path: Local file path
            s3_key: S3 object key

        Returns:
            Tuple of (CloudFront URL, file size in bytes)
        """
        # Get file size
        file_size = os.path.getsize(local_path)

        # Upload to S3
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: self.s3_client.upload_file(
                local_path,
                settings.s3_bucket,
                s3_key,
                ExtraArgs={"ContentType": self._get_content_type(local_path)},
            ),
        )

        # Generate CloudFront URL
        cloudfront_url = f"{settings.cloudfront_url}/{s3_key}"

        return cloudfront_url, file_size

    def _get_content_type(self, file_path: str) -> str:
        """Get content type based on file extension.

        Args:
            file_path: File path

        Returns:
            Content type string
        """
        ext = Path(file_path).suffix.lower()
        content_types = {
            ".mp4": "video/mp4",
            ".mov": "video/quicktime",
            ".webm": "video/webm",
            ".zip": "application/zip",
        }
        return content_types.get(ext, "application/octet-stream")

    def _detect_hardware_encoder(self) -> str | None:
        """Detect available hardware encoder.

        Returns:
            Hardware encoder name or None
        """
        try:
            # Check for NVIDIA NVENC
            result = subprocess.run(
                ["ffmpeg", "-hide_banner", "-encoders"],
                capture_output=True,
                text=True,
                check=False,
            )
            if "h264_nvenc" in result.stdout:
                return "h264_nvenc"
            if "h264_videotoolbox" in result.stdout:
                return "h264_videotoolbox"
        except Exception:
            pass
        return None

    async def extract_segment(
        self,
        input_path: str,
        output_path: str,
        start_time: float,
        end_time: float,
        resolution: Resolution,
        quality: QualityPreset,
        format_type: Format,
        progress_callback: Callable[[int], None] | None = None,
    ) -> None:
        """Extract a single segment from video.

        Args:
            input_path: Input video path
            output_path: Output video path
            start_time: Start time in seconds
            end_time: End time in seconds
            resolution: Output resolution
            quality: Quality preset
            format_type: Output format
            progress_callback: Optional progress callback
        """
        duration = end_time - start_time
        quality_settings = self.QUALITY_PRESETS[quality]
        resolution_settings = self.RESOLUTIONS[resolution]
        format_settings = self.FORMAT_ENCODERS[format_type]

        # Build FFmpeg command
        cmd = [
            "ffmpeg",
            "-y",  # Overwrite output
            "-ss",
            str(start_time),  # Start time
            "-i",
            input_path,  # Input file
            "-t",
            str(duration),  # Duration
            "-vf",
            f"scale={resolution_settings.width}:{resolution_settings.height}",
            "-c:v",
            format_settings["video_codec"],
            "-crf",
            str(quality_settings.crf),
            "-b:v",
            quality_settings.bitrate,
            "-preset",
            quality_settings.preset,
            "-c:a",
            format_settings["audio_codec"],
            "-b:a",
            "192k",
            output_path,
        ]

        # Run FFmpeg
        await self._run_ffmpeg_with_progress(
            cmd, duration=duration, progress_callback=progress_callback
        )

    async def concatenate_segments(
        self,
        input_paths: list[str],
        output_path: str,
        resolution: Resolution,
        quality: QualityPreset,
        format_type: Format,
        progress_callback: Callable[[int], None] | None = None,
    ) -> None:
        """Concatenate multiple video segments into one.

        Args:
            input_paths: List of input video paths
            output_path: Output video path
            resolution: Output resolution
            quality: Quality preset
            format_type: Output format
            progress_callback: Optional progress callback
        """
        if not input_paths:
            raise ValueError("No input paths provided")

        if len(input_paths) == 1:
            # Single file, just copy with re-encoding
            await self.extract_segment(
                input_paths[0],
                output_path,
                0,
                float("inf"),  # Process entire file
                resolution,
                quality,
                format_type,
                progress_callback,
            )
            return

        # Create concat file
        concat_file = tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        )
        try:
            for path in input_paths:
                concat_file.write(f"file '{path}'\n")
            concat_file.close()

            quality_settings = self.QUALITY_PRESETS[quality]
            resolution_settings = self.RESOLUTIONS[resolution]
            format_settings = self.FORMAT_ENCODERS[format_type]

            # Build FFmpeg command for concatenation
            cmd = [
                "ffmpeg",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                concat_file.name,
                "-vf",
                f"scale={resolution_settings.width}:{resolution_settings.height}",
                "-c:v",
                format_settings["video_codec"],
                "-crf",
                str(quality_settings.crf),
                "-b:v",
                quality_settings.bitrate,
                "-preset",
                quality_settings.preset,
                "-c:a",
                format_settings["audio_codec"],
                "-b:a",
                "192k",
                output_path,
            ]

            # Run FFmpeg
            await self._run_ffmpeg_with_progress(
                cmd, progress_callback=progress_callback
            )

        finally:
            # Clean up concat file
            os.unlink(concat_file.name)

    async def process_export(
        self,
        export_id: UUID,
        video: Video,
        segments: list[dict[str, Any]],
        export_type: ExportType,
        resolution: Resolution,
        quality: QualityPreset,
        format_type: Format,
        progress_callback: Callable[[int], None] | None = None,
    ) -> tuple[str, str, int, int]:
        """Process video export.

        Args:
            export_id: Export ID
            video: Source video
            segments: List of segments to export
            export_type: Type of export
            resolution: Output resolution
            quality: Quality preset
            format_type: Output format
            progress_callback: Optional progress callback

        Returns:
            Tuple of (S3 key, CloudFront URL, file size, total duration)
        """
        temp_dir = tempfile.mkdtemp()
        try:
            # Download source video
            source_path = os.path.join(temp_dir, "source.mp4")
            await self.download_video_from_s3(video.s3_key, source_path)

            if export_type == ExportType.SINGLE:
                # Single segment export
                return await self._process_single_export(
                    export_id,
                    source_path,
                    segments[0],
                    resolution,
                    quality,
                    format_type,
                    temp_dir,
                    progress_callback,
                )
            elif export_type == ExportType.COMBINED:
                # Combined segments export
                return await self._process_combined_export(
                    export_id,
                    source_path,
                    segments,
                    resolution,
                    quality,
                    format_type,
                    temp_dir,
                    progress_callback,
                )
            else:  # ExportType.CLIPS
                # Individual clips export (ZIP)
                return await self._process_clips_export(
                    export_id,
                    source_path,
                    segments,
                    resolution,
                    quality,
                    format_type,
                    temp_dir,
                    progress_callback,
                )

        finally:
            # Clean up temp directory
            self._cleanup_directory(temp_dir)

    async def _process_single_export(
        self,
        export_id: UUID,
        source_path: str,
        segment: dict[str, Any],
        resolution: Resolution,
        quality: QualityPreset,
        format_type: Format,
        temp_dir: str,
        progress_callback: Callable[[int], None] | None,
    ) -> tuple[str, str, int, int]:
        """Process single segment export.

        Returns:
            Tuple of (S3 key, CloudFront URL, file size, total duration)
        """
        format_ext = self.FORMAT_ENCODERS[format_type]["container"]
        output_path = os.path.join(temp_dir, f"output.{format_ext}")

        # Extract segment
        await self.extract_segment(
            source_path,
            output_path,
            segment["start_time"],
            segment["end_time"],
            resolution,
            quality,
            format_type,
            progress_callback,
        )

        # Upload to S3
        s3_key = f"exports/{export_id}/video.{format_ext}"
        cloudfront_url, file_size = await self.upload_to_s3(output_path, s3_key)

        total_duration = int(segment["end_time"] - segment["start_time"])

        return s3_key, cloudfront_url, file_size, total_duration

    async def _process_combined_export(
        self,
        export_id: UUID,
        source_path: str,
        segments: list[dict[str, Any]],
        resolution: Resolution,
        quality: QualityPreset,
        format_type: Format,
        temp_dir: str,
        progress_callback: Callable[[int], None] | None,
    ) -> tuple[str, str, int, int]:
        """Process combined segments export.

        Returns:
            Tuple of (S3 key, CloudFront URL, file size, total duration)
        """
        format_ext = self.FORMAT_ENCODERS[format_type]["container"]
        segment_paths = []

        # Extract each segment
        total_duration = 0
        for i, segment in enumerate(segments):
            segment_path = os.path.join(temp_dir, f"segment_{i}.{format_ext}")
            await self.extract_segment(
                source_path,
                segment_path,
                segment["start_time"],
                segment["end_time"],
                resolution,
                quality,
                format_type,
            )
            segment_paths.append(segment_path)
            total_duration += segment["end_time"] - segment["start_time"]

        # Concatenate segments
        output_path = os.path.join(temp_dir, f"combined.{format_ext}")
        await self.concatenate_segments(
            segment_paths,
            output_path,
            resolution,
            quality,
            format_type,
            progress_callback,
        )

        # Upload to S3
        s3_key = f"exports/{export_id}/video.{format_ext}"
        cloudfront_url, file_size = await self.upload_to_s3(output_path, s3_key)

        return s3_key, cloudfront_url, file_size, int(total_duration)

    async def _process_clips_export(
        self,
        export_id: UUID,
        source_path: str,
        segments: list[dict[str, Any]],
        resolution: Resolution,
        quality: QualityPreset,
        format_type: Format,
        temp_dir: str,
        progress_callback: Callable[[int], None] | None,
    ) -> tuple[str, str, int, int]:
        """Process individual clips export (ZIP).

        Returns:
            Tuple of (S3 key, CloudFront URL, file size, total duration)
        """
        format_ext = self.FORMAT_ENCODERS[format_type]["container"]
        clip_paths = []

        # Extract each clip
        total_duration = 0
        for i, segment in enumerate(segments):
            clip_path = os.path.join(temp_dir, f"clip_{i+1}.{format_ext}")
            await self.extract_segment(
                source_path,
                clip_path,
                segment["start_time"],
                segment["end_time"],
                resolution,
                quality,
                format_type,
            )
            clip_paths.append(clip_path)
            total_duration += segment["end_time"] - segment["start_time"]

        # Create ZIP archive
        zip_path = os.path.join(temp_dir, "clips.zip")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for clip_path in clip_paths:
                zipf.write(clip_path, os.path.basename(clip_path))

        # Upload to S3
        s3_key = f"exports/{export_id}/clips.zip"
        cloudfront_url, file_size = await self.upload_to_s3(zip_path, s3_key)

        return s3_key, cloudfront_url, file_size, int(total_duration)

    async def _run_ffmpeg_with_progress(
        self,
        cmd: list[str],
        duration: float | None = None,
        progress_callback: Callable[[int], None] | None = None,
    ) -> None:
        """Run FFmpeg command with progress tracking.

        Args:
            cmd: FFmpeg command
            duration: Expected duration in seconds
            progress_callback: Optional progress callback
        """
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        # Wait for process to complete
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            error_msg = stderr.decode() if stderr else "Unknown FFmpeg error"
            raise RuntimeError(f"FFmpeg failed: {error_msg}")

    def _cleanup_directory(self, directory: str) -> None:
        """Clean up temporary directory.

        Args:
            directory: Directory path to clean up
        """
        try:
            import shutil

            shutil.rmtree(directory)
        except Exception:
            pass  # Best effort cleanup
