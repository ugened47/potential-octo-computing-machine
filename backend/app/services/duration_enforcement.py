"""Duration enforcement service for trimming videos to platform limits."""

import logging
import subprocess
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class TrimStrategy(str, Enum):
    """Video trimming strategies."""

    TRIM_START = "trim_start"  # Keep last N seconds
    TRIM_END = "trim_end"  # Keep first N seconds
    SMART_TRIM = "smart_trim"  # Use highlight scores
    USER_SELECTION = "user_selection"  # Manual segment selection


class DurationEnforcementService:
    """Service for enforcing video duration limits."""

    def __init__(self):
        """Initialize duration enforcement service."""
        self.logger = logging.getLogger(__name__)

    async def get_video_duration(self, video_path: str) -> float:
        """Get video duration in seconds.

        Args:
            video_path: Path to video file

        Returns:
            Duration in seconds

        Raises:
            RuntimeError: If ffprobe command fails
        """
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            video_path,
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            duration = float(result.stdout.strip())
            return duration
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to get video duration: {e.stderr}") from e
        except ValueError as e:
            raise RuntimeError(f"Failed to parse duration: {result.stdout}") from e

    async def trim_video(
        self,
        input_path: str,
        output_path: str,
        max_duration_seconds: int,
        strategy: TrimStrategy = TrimStrategy.TRIM_END,
        segment_start: float | None = None,
        segment_end: float | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Trim video to meet duration limit.

        Args:
            input_path: Path to input video file
            output_path: Path to output video file
            max_duration_seconds: Maximum duration in seconds
            strategy: Trimming strategy to use
            segment_start: Start time for USER_SELECTION strategy (seconds)
            segment_end: End time for USER_SELECTION strategy (seconds)
            **kwargs: Additional strategy-specific options (e.g., highlight_scores)

        Returns:
            Dictionary with trim metadata

        Raises:
            ValueError: If inputs are invalid
            RuntimeError: If FFmpeg command fails
        """
        # Get current video duration
        current_duration = await self.get_video_duration(input_path)

        # Check if trimming is needed
        if current_duration <= max_duration_seconds:
            self.logger.info(f"Video duration ({current_duration}s) is within limit ({max_duration_seconds}s)")
            # Just copy the file without trimming
            await self._copy_video(input_path, output_path)
            return {
                "original_duration": current_duration,
                "trimmed_duration": current_duration,
                "trim_start_time": 0.0,
                "trim_end_time": current_duration,
                "trimming_required": False,
            }

        # Determine trim times based on strategy
        if strategy == TrimStrategy.TRIM_START:
            # Keep last N seconds
            start_time = max(0, current_duration - max_duration_seconds)
            end_time = current_duration
        elif strategy == TrimStrategy.TRIM_END:
            # Keep first N seconds
            start_time = 0.0
            end_time = min(current_duration, max_duration_seconds)
        elif strategy == TrimStrategy.USER_SELECTION:
            # Use user-specified segment
            if segment_start is None or segment_end is None:
                raise ValueError("segment_start and segment_end required for USER_SELECTION strategy")
            if segment_start < 0 or segment_end > current_duration or segment_start >= segment_end:
                raise ValueError(f"Invalid segment times: {segment_start}-{segment_end}s for {current_duration}s video")

            # Ensure segment is within duration limit
            segment_duration = segment_end - segment_start
            if segment_duration > max_duration_seconds:
                # Trim to max duration from start of segment
                start_time = segment_start
                end_time = segment_start + max_duration_seconds
            else:
                start_time = segment_start
                end_time = segment_end
        elif strategy == TrimStrategy.SMART_TRIM:
            # Use highlight scores to find best segment
            start_time, end_time = await self._smart_trim(
                current_duration, max_duration_seconds, **kwargs
            )
        else:
            raise ValueError(f"Unknown strategy: {strategy}")

        # Perform the trim
        await self._trim_segment(input_path, output_path, start_time, end_time)

        trimmed_duration = end_time - start_time

        return {
            "original_duration": current_duration,
            "trimmed_duration": trimmed_duration,
            "trim_start_time": start_time,
            "trim_end_time": end_time,
            "trimming_required": True,
            "strategy": strategy.value,
        }

    async def _smart_trim(
        self,
        current_duration: float,
        max_duration: int,
        **kwargs: Any,
    ) -> tuple[float, float]:
        """Find best segment using highlight scores or audio analysis.

        Args:
            current_duration: Current video duration in seconds
            max_duration: Maximum duration allowed
            **kwargs: Additional options (highlight_scores, audio_energy)

        Returns:
            Tuple of (start_time, end_time)
        """
        highlight_scores = kwargs.get("highlight_scores")

        if highlight_scores:
            # Find highest-scoring continuous segment
            # This is a simplified implementation
            # In production, you'd analyze highlight scores to find the best segment
            # For now, use middle segment as it often contains the best content
            center = current_duration / 2
            start_time = max(0, center - (max_duration / 2))
            end_time = min(current_duration, start_time + max_duration)
        else:
            # Fallback: use middle segment
            # TODO: Implement audio energy analysis
            center = current_duration / 2
            start_time = max(0, center - (max_duration / 2))
            end_time = min(current_duration, start_time + max_duration)

        return (start_time, end_time)

    async def _trim_segment(
        self,
        input_path: str,
        output_path: str,
        start_time: float,
        end_time: float,
    ) -> None:
        """Trim video segment using FFmpeg.

        Args:
            input_path: Input video path
            output_path: Output video path
            start_time: Start time in seconds
            end_time: End time in seconds

        Raises:
            RuntimeError: If FFmpeg command fails
        """
        duration = end_time - start_time

        cmd = [
            "ffmpeg",
            "-i", input_path,
            "-ss", str(start_time),
            "-t", str(duration),
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "192k",
            "-movflags", "+faststart",
            "-y",
            output_path,
        ]

        try:
            self.logger.info(f"Trimming video: {start_time}s to {end_time}s ({duration}s)")
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            self.logger.info("Video trimming completed successfully")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"FFmpeg trim failed: {e.stderr}")
            raise RuntimeError(f"FFmpeg trim failed: {e.stderr}") from e

    async def _copy_video(self, input_path: str, output_path: str) -> None:
        """Copy video without re-encoding (stream copy).

        Args:
            input_path: Input video path
            output_path: Output video path

        Raises:
            RuntimeError: If FFmpeg command fails
        """
        cmd = [
            "ffmpeg",
            "-i", input_path,
            "-c", "copy",
            "-movflags", "+faststart",
            "-y",
            output_path,
        ]

        try:
            self.logger.info("Copying video without trimming")
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            self.logger.info("Video copy completed successfully")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"FFmpeg copy failed: {e.stderr}")
            raise RuntimeError(f"FFmpeg copy failed: {e.stderr}") from e

    def validate_segment_times(
        self,
        video_duration: float,
        start_time: float | None,
        end_time: float | None,
    ) -> tuple[bool, str | None]:
        """Validate segment times against video duration.

        Args:
            video_duration: Total video duration in seconds
            start_time: Segment start time (can be None)
            end_time: Segment end time (can be None)

        Returns:
            Tuple of (is_valid, error_message)
        """
        if start_time is None or end_time is None:
            return (True, None)

        if start_time < 0:
            return (False, "Start time cannot be negative")

        if end_time > video_duration:
            return (False, f"End time ({end_time}s) exceeds video duration ({video_duration}s)")

        if start_time >= end_time:
            return (False, f"Start time ({start_time}s) must be before end time ({end_time}s)")

        return (True, None)
