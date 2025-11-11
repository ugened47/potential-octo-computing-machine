"""Video transformation service for aspect ratio conversion."""

import logging
import os
import subprocess
import tempfile
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class AspectRatioStrategy(str, Enum):
    """Aspect ratio conversion strategies."""

    SMART = "smart"  # Smart crop with face/motion detection
    CENTER = "center"  # Simple center crop
    LETTERBOX = "letterbox"  # Add letterbox bars
    BLUR = "blur"  # Blur background with scaled video


class VideoTransformationService:
    """Service for video aspect ratio transformation."""

    def __init__(self):
        """Initialize transformation service."""
        self.logger = logging.getLogger(__name__)

    def parse_aspect_ratio(self, aspect_ratio: str) -> tuple[int, int]:
        """Parse aspect ratio string to width:height tuple.

        Args:
            aspect_ratio: Aspect ratio string (e.g., "9:16", "16:9")

        Returns:
            Tuple of (width, height) as integers

        Raises:
            ValueError: If aspect ratio format is invalid
        """
        try:
            parts = aspect_ratio.split(":")
            if len(parts) != 2:
                raise ValueError(f"Invalid aspect ratio format: {aspect_ratio}")
            width = int(parts[0])
            height = int(parts[1])
            if width <= 0 or height <= 0:
                raise ValueError(f"Aspect ratio dimensions must be positive: {aspect_ratio}")
            return (width, height)
        except (ValueError, IndexError) as e:
            raise ValueError(f"Invalid aspect ratio format: {aspect_ratio}") from e

    def calculate_dimensions(
        self,
        input_width: int,
        input_height: int,
        target_aspect: tuple[int, int],
    ) -> tuple[int, int]:
        """Calculate output dimensions based on target aspect ratio.

        Args:
            input_width: Input video width
            input_height: Input video height
            target_aspect: Target aspect ratio as (width, height) tuple

        Returns:
            Tuple of (output_width, output_height)
        """
        target_ratio = target_aspect[0] / target_aspect[1]
        input_ratio = input_width / input_height

        # Determine output dimensions (standardize to 1080p variants)
        if target_ratio > 1:  # Landscape (16:9, etc.)
            output_width = 1920
            output_height = int(output_width / target_ratio)
        elif target_ratio < 1:  # Portrait (9:16, etc.)
            output_height = 1920
            output_width = int(output_height * target_ratio)
        else:  # Square (1:1)
            output_width = output_height = 1080

        return (output_width, output_height)

    async def transform_aspect_ratio(
        self,
        input_path: str,
        output_path: str,
        target_aspect_ratio: str,
        strategy: AspectRatioStrategy = AspectRatioStrategy.BLUR,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Transform video to target aspect ratio using specified strategy.

        Args:
            input_path: Path to input video file
            output_path: Path to output video file
            target_aspect_ratio: Target aspect ratio (e.g., "9:16")
            strategy: Transformation strategy to use
            **kwargs: Additional strategy-specific options

        Returns:
            Dictionary with transformation metadata

        Raises:
            ValueError: If inputs are invalid
            RuntimeError: If FFmpeg command fails
        """
        if not os.path.exists(input_path):
            raise ValueError(f"Input file does not exist: {input_path}")

        # Parse aspect ratio
        target_aspect = self.parse_aspect_ratio(target_aspect_ratio)

        # Get input video dimensions using ffprobe
        probe_result = await self._probe_video(input_path)
        input_width = probe_result["width"]
        input_height = probe_result["height"]

        # Calculate output dimensions
        output_width, output_height = self.calculate_dimensions(
            input_width, input_height, target_aspect
        )

        # Apply transformation based on strategy
        if strategy == AspectRatioStrategy.SMART:
            await self._smart_crop(
                input_path, output_path, input_width, input_height, output_width, output_height, **kwargs
            )
        elif strategy == AspectRatioStrategy.CENTER:
            await self._center_crop(
                input_path, output_path, input_width, input_height, output_width, output_height, **kwargs
            )
        elif strategy == AspectRatioStrategy.LETTERBOX:
            await self._letterbox(
                input_path, output_path, input_width, input_height, output_width, output_height, **kwargs
            )
        elif strategy == AspectRatioStrategy.BLUR:
            await self._blur_background(
                input_path, output_path, input_width, input_height, output_width, output_height, **kwargs
            )
        else:
            raise ValueError(f"Unknown strategy: {strategy}")

        return {
            "input_resolution": f"{input_width}x{input_height}",
            "output_resolution": f"{output_width}x{output_height}",
            "target_aspect_ratio": target_aspect_ratio,
            "strategy": strategy.value,
        }

    async def _probe_video(self, video_path: str) -> dict[str, int]:
        """Probe video file to get dimensions.

        Args:
            video_path: Path to video file

        Returns:
            Dictionary with width and height

        Raises:
            RuntimeError: If ffprobe command fails
        """
        cmd = [
            "ffprobe",
            "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height",
            "-of", "csv=p=0",
            video_path,
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            width, height = map(int, result.stdout.strip().split(","))
            return {"width": width, "height": height}
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to probe video: {e.stderr}") from e
        except (ValueError, IndexError) as e:
            raise RuntimeError(f"Failed to parse probe output: {result.stdout}") from e

    async def _smart_crop(
        self,
        input_path: str,
        output_path: str,
        in_w: int,
        in_h: int,
        out_w: int,
        out_h: int,
        **kwargs: Any,
    ) -> None:
        """Apply smart crop using face/motion detection.

        Note: This is a simplified implementation. Full implementation would use
        face detection (OpenCV/MediaPipe) to track faces across frames.

        Args:
            input_path: Input video path
            output_path: Output video path
            in_w: Input width
            in_h: Input height
            out_w: Output width
            out_h: Output height
            **kwargs: Additional options
        """
        # For now, use center crop as fallback
        # TODO: Implement face detection with OpenCV/MediaPipe
        await self._center_crop(input_path, output_path, in_w, in_h, out_w, out_h, **kwargs)

    async def _center_crop(
        self,
        input_path: str,
        output_path: str,
        in_w: int,
        in_h: int,
        out_w: int,
        out_h: int,
        **kwargs: Any,
    ) -> None:
        """Apply center crop transformation.

        Args:
            input_path: Input video path
            output_path: Output video path
            in_w: Input width
            in_h: Input height
            out_w: Output width
            out_h: Output height
            **kwargs: Additional options (crop_position_bias)
        """
        # Calculate crop dimensions
        in_aspect = in_w / in_h
        out_aspect = out_w / out_h

        if in_aspect > out_aspect:
            # Input is wider, crop width
            crop_w = int(in_h * out_aspect)
            crop_h = in_h
            crop_x = (in_w - crop_w) // 2
            crop_y = 0
        else:
            # Input is taller, crop height
            crop_w = in_w
            crop_h = int(in_w / out_aspect)
            crop_x = 0
            crop_y = (in_h - crop_h) // 2

        # Apply position bias if specified
        position_bias = kwargs.get("crop_position_bias", "center")
        if position_bias == "top" and crop_y > 0:
            crop_y = 0
        elif position_bias == "bottom" and crop_y > 0:
            crop_y = in_h - crop_h

        # Build FFmpeg command with center crop
        cmd = [
            "ffmpeg",
            "-i", input_path,
            "-vf", f"crop={crop_w}:{crop_h}:{crop_x}:{crop_y},scale={out_w}:{out_h}",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "192k",
            "-movflags", "+faststart",
            "-y",
            output_path,
        ]

        await self._run_ffmpeg(cmd)

    async def _letterbox(
        self,
        input_path: str,
        output_path: str,
        in_w: int,
        in_h: int,
        out_w: int,
        out_h: int,
        **kwargs: Any,
    ) -> None:
        """Apply letterbox transformation.

        Args:
            input_path: Input video path
            output_path: Output video path
            in_w: Input width
            in_h: Input height
            out_w: Output width
            out_h: Output height
            **kwargs: Additional options (letterbox_color)
        """
        letterbox_color = kwargs.get("letterbox_color", "black")

        # Build FFmpeg command with letterbox
        cmd = [
            "ffmpeg",
            "-i", input_path,
            "-vf", f"scale={out_w}:{out_h}:force_original_aspect_ratio=decrease,pad={out_w}:{out_h}:(ow-iw)/2:(oh-ih)/2:color={letterbox_color}",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "192k",
            "-movflags", "+faststart",
            "-y",
            output_path,
        ]

        await self._run_ffmpeg(cmd)

    async def _blur_background(
        self,
        input_path: str,
        output_path: str,
        in_w: int,
        in_h: int,
        out_w: int,
        out_h: int,
        **kwargs: Any,
    ) -> None:
        """Apply blur background transformation.

        Args:
            input_path: Input video path
            output_path: Output video path
            in_w: Input width
            in_h: Input height
            out_w: Output width
            out_h: Output height
            **kwargs: Additional options (blur_intensity)
        """
        blur_intensity = kwargs.get("blur_intensity", 20)

        # Build FFmpeg command with blur background
        # Split video, blur and scale one copy as background, overlay scaled original
        filter_complex = (
            f"[0:v]split=2[bg][fg];"
            f"[bg]scale={out_w}:{out_h},gblur=sigma={blur_intensity}[blurred];"
            f"[fg]scale={out_w}:{out_h}:force_original_aspect_ratio=decrease[scaled];"
            f"[blurred][scaled]overlay=(W-w)/2:(H-h)/2"
        )

        cmd = [
            "ffmpeg",
            "-i", input_path,
            "-filter_complex", filter_complex,
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "192k",
            "-movflags", "+faststart",
            "-y",
            output_path,
        ]

        await self._run_ffmpeg(cmd)

    async def _run_ffmpeg(self, cmd: list[str]) -> None:
        """Run FFmpeg command.

        Args:
            cmd: FFmpeg command as list of arguments

        Raises:
            RuntimeError: If FFmpeg command fails
        """
        try:
            self.logger.info(f"Running FFmpeg: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            self.logger.info("FFmpeg completed successfully")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"FFmpeg failed: {e.stderr}")
            raise RuntimeError(f"FFmpeg transformation failed: {e.stderr}") from e
