"""Video transformation service for aspect ratio conversion."""

import asyncio
import logging
import subprocess
from pathlib import Path
from typing import Literal

logger = logging.getLogger(__name__)


class VideoTransformationService:
    """Service for handling video aspect ratio transformations."""

    @staticmethod
    async def transform_aspect_ratio(
        input_path: str,
        output_path: str,
        target_aspect_ratio: str,
        strategy: Literal["smart", "center", "letterbox", "blur"] = "smart",
        target_resolution: str = "1080x1920",
    ) -> bool:
        """Transform video to target aspect ratio using specified strategy.

        Args:
            input_path: Path to input video file
            output_path: Path to output video file
            target_aspect_ratio: Target aspect ratio (e.g., "9:16", "16:9", "1:1")
            strategy: Transformation strategy (smart, center, letterbox, blur)
            target_resolution: Target resolution (e.g., "1080x1920")

        Returns:
            bool: True if transformation succeeded, False otherwise
        """
        try:
            logger.info(
                f"Transforming video aspect ratio: {input_path} -> {output_path} "
                f"(target: {target_aspect_ratio}, strategy: {strategy})"
            )

            # Parse target resolution
            width, height = map(int, target_resolution.split("x"))

            # Select transformation strategy
            if strategy == "smart":
                return await VideoTransformationService._smart_crop(
                    input_path, output_path, width, height
                )
            elif strategy == "center":
                return await VideoTransformationService._center_crop(
                    input_path, output_path, width, height
                )
            elif strategy == "letterbox":
                return await VideoTransformationService._letterbox(
                    input_path, output_path, width, height
                )
            elif strategy == "blur":
                return await VideoTransformationService._blur_background(
                    input_path, output_path, width, height
                )
            else:
                logger.error(f"Unknown transformation strategy: {strategy}")
                return False

        except Exception as e:
            logger.error(f"Error transforming video aspect ratio: {e}")
            return False

    @staticmethod
    async def _smart_crop(
        input_path: str, output_path: str, width: int, height: int
    ) -> bool:
        """Apply smart crop using face detection and motion tracking.

        For now, falls back to center crop. Full implementation would use:
        - OpenCV or MediaPipe for face detection
        - Motion tracking across frames
        - Smooth crop transitions

        Args:
            input_path: Input video path
            output_path: Output video path
            width: Target width
            height: Target height

        Returns:
            bool: True if successful
        """
        # TODO: Implement face detection and motion tracking
        # For now, use center crop as fallback
        logger.info("Smart crop: Using center crop (face detection not yet implemented)")
        return await VideoTransformationService._center_crop(
            input_path, output_path, width, height
        )

    @staticmethod
    async def _center_crop(
        input_path: str, output_path: str, width: int, height: int
    ) -> bool:
        """Apply center crop to video.

        Args:
            input_path: Input video path
            output_path: Output video path
            width: Target width
            height: Target height

        Returns:
            bool: True if successful
        """
        try:
            # FFmpeg command for center crop and scale
            cmd = [
                "ffmpeg",
                "-i",
                input_path,
                "-vf",
                f"scale={width}:{height}:force_original_aspect_ratio=increase,"
                f"crop={width}:{height}",
                "-c:a",
                "copy",  # Copy audio without re-encoding
                "-y",  # Overwrite output file
                output_path,
            ]

            # Run FFmpeg command
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                logger.error(f"FFmpeg center crop failed: {stderr.decode()}")
                return False

            logger.info(f"Center crop successful: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Error in center crop: {e}")
            return False

    @staticmethod
    async def _letterbox(
        input_path: str, output_path: str, width: int, height: int
    ) -> bool:
        """Apply letterbox/pillarbox to fit video in target dimensions.

        Args:
            input_path: Input video path
            output_path: Output video path
            width: Target width
            height: Target height

        Returns:
            bool: True if successful
        """
        try:
            # FFmpeg command for letterbox
            cmd = [
                "ffmpeg",
                "-i",
                input_path,
                "-vf",
                f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
                f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black",
                "-c:a",
                "copy",
                "-y",
                output_path,
            ]

            # Run FFmpeg command
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                logger.error(f"FFmpeg letterbox failed: {stderr.decode()}")
                return False

            logger.info(f"Letterbox successful: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Error in letterbox: {e}")
            return False

    @staticmethod
    async def _blur_background(
        input_path: str, output_path: str, width: int, height: int
    ) -> bool:
        """Apply blur background strategy - scale video and use blurred version as background.

        Args:
            input_path: Input video path
            output_path: Output video path
            width: Target width
            height: Target height

        Returns:
            bool: True if successful
        """
        try:
            # Complex FFmpeg filter for blur background
            # 1. Scale original to fit within target dimensions
            # 2. Create blurred background from same video
            # 3. Overlay scaled video on blurred background
            filter_complex = (
                f"[0:v]scale={width}:{height}:force_original_aspect_ratio=decrease[scaled];"
                f"[0:v]scale={width}:{height}:force_original_aspect_ratio=increase,"
                f"crop={width}:{height},boxblur=20:10[blurred];"
                f"[blurred][scaled]overlay=(W-w)/2:(H-h)/2"
            )

            cmd = [
                "ffmpeg",
                "-i",
                input_path,
                "-filter_complex",
                filter_complex,
                "-c:a",
                "copy",
                "-y",
                output_path,
            ]

            # Run FFmpeg command
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                logger.error(f"FFmpeg blur background failed: {stderr.decode()}")
                return False

            logger.info(f"Blur background successful: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Error in blur background: {e}")
            return False

    @staticmethod
    def parse_aspect_ratio(aspect_ratio: str) -> tuple[int, int]:
        """Parse aspect ratio string to width:height tuple.

        Args:
            aspect_ratio: Aspect ratio string (e.g., "9:16", "16:9")

        Returns:
            Tuple of (width_ratio, height_ratio)
        """
        parts = aspect_ratio.split(":")
        if len(parts) != 2:
            raise ValueError(f"Invalid aspect ratio format: {aspect_ratio}")
        return int(parts[0]), int(parts[1])

    @staticmethod
    def calculate_target_resolution(
        aspect_ratio: str, target_height: int = 1920
    ) -> str:
        """Calculate target resolution from aspect ratio and height.

        Args:
            aspect_ratio: Aspect ratio string (e.g., "9:16")
            target_height: Target height in pixels

        Returns:
            Resolution string (e.g., "1080x1920")
        """
        width_ratio, height_ratio = VideoTransformationService.parse_aspect_ratio(
            aspect_ratio
        )
        target_width = int(target_height * width_ratio / height_ratio)
        return f"{target_width}x{target_height}"
