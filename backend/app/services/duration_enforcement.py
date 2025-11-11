"""Duration enforcement service for trimming videos to platform limits."""

import asyncio
import logging
from typing import Literal

logger = logging.getLogger(__name__)


class DurationEnforcementService:
    """Service for enforcing video duration limits."""

    @staticmethod
    async def trim_video(
        input_path: str,
        output_path: str,
        max_duration: int,
        strategy: Literal["trim_start", "trim_end", "smart", "segment"] = "trim_end",
        segment_start: float | None = None,
        segment_end: float | None = None,
        video_duration: float | None = None,
    ) -> dict:
        """Trim video to meet platform duration requirements.

        Args:
            input_path: Path to input video file
            output_path: Path to output video file
            max_duration: Maximum duration in seconds
            strategy: Trimming strategy
            segment_start: Start time for segment strategy (seconds)
            segment_end: End time for segment strategy (seconds)
            video_duration: Total video duration in seconds

        Returns:
            dict: Trim metadata including start_time, end_time, duration
        """
        try:
            logger.info(
                f"Trimming video: {input_path} -> {output_path} "
                f"(max: {max_duration}s, strategy: {strategy})"
            )

            # Get video duration if not provided
            if video_duration is None:
                video_duration = await DurationEnforcementService._get_duration(
                    input_path
                )

            # Check if trimming is needed
            if video_duration <= max_duration:
                logger.info(
                    f"Video duration ({video_duration}s) within limit ({max_duration}s). "
                    "No trimming needed."
                )
                # Copy file without trimming
                await DurationEnforcementService._copy_video(input_path, output_path)
                return {
                    "original_duration": video_duration,
                    "trimmed_duration": video_duration,
                    "trim_start_time": 0,
                    "trim_end_time": video_duration,
                    "trimmed": False,
                }

            # Calculate trim times based on strategy
            if strategy == "trim_end":
                start_time = 0
                end_time = max_duration
            elif strategy == "trim_start":
                start_time = video_duration - max_duration
                end_time = video_duration
            elif strategy == "segment":
                if segment_start is None or segment_end is None:
                    raise ValueError("segment_start and segment_end required for segment strategy")
                start_time = segment_start
                end_time = min(segment_end, segment_start + max_duration)
            elif strategy == "smart":
                # TODO: Implement smart trimming using highlight scores
                # For now, fall back to trim_end
                logger.info("Smart trim: Using trim_end (highlight scores not available)")
                start_time = 0
                end_time = max_duration
            else:
                raise ValueError(f"Unknown trim strategy: {strategy}")

            # Perform trimming
            success = await DurationEnforcementService._trim_segment(
                input_path, output_path, start_time, end_time
            )

            if not success:
                raise Exception("Trimming failed")

            trimmed_duration = end_time - start_time

            return {
                "original_duration": video_duration,
                "trimmed_duration": trimmed_duration,
                "trim_start_time": start_time,
                "trim_end_time": end_time,
                "trimmed": True,
            }

        except Exception as e:
            logger.error(f"Error trimming video: {e}")
            raise

    @staticmethod
    async def _get_duration(input_path: str) -> float:
        """Get video duration using FFprobe.

        Args:
            input_path: Path to video file

        Returns:
            float: Duration in seconds
        """
        try:
            cmd = [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                input_path,
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                raise Exception(f"FFprobe failed: {stderr.decode()}")

            duration = float(stdout.decode().strip())
            return duration

        except Exception as e:
            logger.error(f"Error getting video duration: {e}")
            raise

    @staticmethod
    async def _trim_segment(
        input_path: str, output_path: str, start_time: float, end_time: float
    ) -> bool:
        """Trim video segment using FFmpeg.

        Args:
            input_path: Input video path
            output_path: Output video path
            start_time: Start time in seconds
            end_time: End time in seconds

        Returns:
            bool: True if successful
        """
        try:
            duration = end_time - start_time

            cmd = [
                "ffmpeg",
                "-i",
                input_path,
                "-ss",
                str(start_time),
                "-t",
                str(duration),
                "-c",
                "copy",  # Copy without re-encoding for speed
                "-y",
                output_path,
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                logger.error(f"FFmpeg trim failed: {stderr.decode()}")
                return False

            logger.info(f"Trim successful: {output_path} ({start_time}s - {end_time}s)")
            return True

        except Exception as e:
            logger.error(f"Error trimming segment: {e}")
            return False

    @staticmethod
    async def _copy_video(input_path: str, output_path: str) -> bool:
        """Copy video without modification.

        Args:
            input_path: Input video path
            output_path: Output video path

        Returns:
            bool: True if successful
        """
        try:
            cmd = [
                "ffmpeg",
                "-i",
                input_path,
                "-c",
                "copy",
                "-y",
                output_path,
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                logger.error(f"FFmpeg copy failed: {stderr.decode()}")
                return False

            logger.info(f"Copy successful: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Error copying video: {e}")
            return False

    @staticmethod
    def validate_segment_times(
        segment_start: float | None,
        segment_end: float | None,
        video_duration: float,
    ) -> bool:
        """Validate segment start and end times.

        Args:
            segment_start: Start time in seconds
            segment_end: End time in seconds
            video_duration: Total video duration in seconds

        Returns:
            bool: True if valid

        Raises:
            ValueError: If segment times are invalid
        """
        if segment_start is not None and segment_end is not None:
            if segment_start < 0:
                raise ValueError("segment_start must be non-negative")
            if segment_end < 0:
                raise ValueError("segment_end must be non-negative")
            if segment_start >= segment_end:
                raise ValueError("segment_start must be less than segment_end")
            if segment_end > video_duration:
                raise ValueError("segment_end exceeds video duration")

        return True
