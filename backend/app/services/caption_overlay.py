"""Caption overlay service for burning captions into video."""

import logging
import os
import subprocess
import tempfile
from typing import Any

logger = logging.getLogger(__name__)


class CaptionOverlayService:
    """Service for overlaying captions on video."""

    def __init__(self):
        """Initialize caption overlay service."""
        self.logger = logging.getLogger(__name__)

    async def add_captions(
        self,
        input_path: str,
        output_path: str,
        transcript_words: list[dict[str, Any]],
        caption_style: dict[str, Any],
        video_height: int = 1920,
    ) -> dict[str, Any]:
        """Add captions to video using transcript word-level timestamps.

        Args:
            input_path: Path to input video file
            output_path: Path to output video file
            transcript_words: List of word dictionaries with 'word', 'start', 'end' keys
            caption_style: Caption styling configuration
            video_height: Video height for font size calculation

        Returns:
            Dictionary with caption metadata

        Raises:
            ValueError: If inputs are invalid
            RuntimeError: If FFmpeg command fails
        """
        if not transcript_words:
            # No captions to add, just copy the video
            await self._copy_video(input_path, output_path)
            return {
                "captions_added": False,
                "caption_count": 0,
                "message": "No transcript data available",
            }

        # Parse transcript into caption chunks
        caption_chunks = self._create_caption_chunks(transcript_words, caption_style)

        # Generate SRT subtitle file
        srt_path = await self._generate_srt(caption_chunks)

        try:
            # Burn captions into video using FFmpeg
            await self._burn_captions(
                input_path, output_path, srt_path, caption_style, video_height
            )

            return {
                "captions_added": True,
                "caption_count": len(caption_chunks),
                "total_duration": caption_chunks[-1]["end"] if caption_chunks else 0,
            }
        finally:
            # Clean up temporary SRT file
            if os.path.exists(srt_path):
                os.remove(srt_path)

    def _create_caption_chunks(
        self,
        transcript_words: list[dict[str, Any]],
        caption_style: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Parse transcript into caption chunks.

        Args:
            transcript_words: List of word dictionaries with 'word', 'start', 'end'
            caption_style: Caption styling configuration

        Returns:
            List of caption chunks with 'text', 'start', 'end' keys
        """
        max_chars_per_line = caption_style.get("max_chars_per_line", 30)
        max_lines = caption_style.get("max_lines", 2)
        min_duration = 0.8  # Minimum caption duration in seconds

        chunks = []
        current_chunk_words = []
        current_chunk_chars = 0
        chunk_start_time = None

        for word_data in transcript_words:
            word = word_data["word"].strip()
            word_start = word_data["start"]
            word_end = word_data["end"]

            if not word:
                continue

            # Initialize chunk start time
            if chunk_start_time is None:
                chunk_start_time = word_start

            # Check if adding this word would exceed character limit
            word_length = len(word) + 1  # +1 for space
            if current_chunk_chars + word_length > max_chars_per_line and current_chunk_words:
                # Save current chunk and start new one
                chunk_text = " ".join(current_chunk_words)
                chunk_end = word_start
                chunk_duration = chunk_end - chunk_start_time

                # Ensure minimum duration
                if chunk_duration < min_duration:
                    chunk_end = chunk_start_time + min_duration

                chunks.append({
                    "text": chunk_text,
                    "start": chunk_start_time,
                    "end": chunk_end,
                })

                # Start new chunk
                current_chunk_words = [word]
                current_chunk_chars = word_length
                chunk_start_time = word_start
            else:
                # Add word to current chunk
                current_chunk_words.append(word)
                current_chunk_chars += word_length

        # Add final chunk if any
        if current_chunk_words:
            chunk_text = " ".join(current_chunk_words)
            chunk_end = transcript_words[-1]["end"]
            chunks.append({
                "text": chunk_text,
                "start": chunk_start_time,
                "end": chunk_end,
            })

        return chunks

    async def _generate_srt(self, caption_chunks: list[dict[str, Any]]) -> str:
        """Generate SRT subtitle file from caption chunks.

        Args:
            caption_chunks: List of caption chunks

        Returns:
            Path to generated SRT file
        """
        # Create temporary SRT file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".srt", delete=False, encoding="utf-8") as f:
            srt_path = f.name

            for i, chunk in enumerate(caption_chunks, 1):
                # SRT format:
                # 1
                # 00:00:00,000 --> 00:00:02,000
                # Caption text here
                start_time = self._format_srt_time(chunk["start"])
                end_time = self._format_srt_time(chunk["end"])

                f.write(f"{i}\n")
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{chunk['text']}\n")
                f.write("\n")

        return srt_path

    def _format_srt_time(self, seconds: float) -> str:
        """Format time in seconds to SRT format (HH:MM:SS,mmm).

        Args:
            seconds: Time in seconds

        Returns:
            Formatted time string
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)

        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    async def _burn_captions(
        self,
        input_path: str,
        output_path: str,
        srt_path: str,
        caption_style: dict[str, Any],
        video_height: int,
    ) -> None:
        """Burn captions into video using FFmpeg subtitles filter.

        Args:
            input_path: Input video path
            output_path: Output video path
            srt_path: Path to SRT subtitle file
            caption_style: Caption styling configuration
            video_height: Video height for font size calculation

        Raises:
            RuntimeError: If FFmpeg command fails
        """
        # Extract style properties
        font_family = caption_style.get("font_family", "Arial")
        font_size_percent = caption_style.get("font_size", 5)
        font_size = int(video_height * (font_size_percent / 100))
        font_weight = caption_style.get("font_weight", "bold")
        text_color = caption_style.get("text_color", "#FFFFFF")
        background_color = caption_style.get("background_color", "#000000CC")
        stroke_color = caption_style.get("stroke_color", "#000000")
        stroke_width = caption_style.get("stroke_width", 2)
        alignment = caption_style.get("alignment", "center")
        y_offset = caption_style.get("y_offset", 85)

        # Convert hex colors to FFmpeg format (without #)
        primary_color = self._hex_to_ffmpeg_color(text_color)
        back_color = self._hex_to_ffmpeg_color(background_color)
        outline_color = self._hex_to_ffmpeg_color(stroke_color)

        # Calculate margin based on y_offset percentage
        margin_v = int(video_height * ((100 - y_offset) / 100))

        # Build subtitle style string (ASS format)
        # Note: FFmpeg subtitles filter uses ASS format internally
        subtitle_style = (
            f"FontName={font_family},"
            f"FontSize={font_size},"
            f"PrimaryColour={primary_color},"
            f"BackColour={back_color},"
            f"OutlineColour={outline_color},"
            f"Outline={stroke_width},"
            f"MarginV={margin_v},"
            f"Alignment=2"  # Bottom center alignment
        )

        # Escape special characters in SRT path for FFmpeg
        srt_path_escaped = srt_path.replace("\\", "\\\\").replace(":", "\\:")

        # Build FFmpeg command
        cmd = [
            "ffmpeg",
            "-i", input_path,
            "-vf", f"subtitles={srt_path_escaped}:force_style='{subtitle_style}'",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-c:a", "copy",  # Copy audio without re-encoding
            "-movflags", "+faststart",
            "-y",
            output_path,
        ]

        try:
            self.logger.info("Burning captions into video")
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            self.logger.info("Caption burning completed successfully")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"FFmpeg caption burn failed: {e.stderr}")
            raise RuntimeError(f"FFmpeg caption burn failed: {e.stderr}") from e

    def _hex_to_ffmpeg_color(self, hex_color: str) -> str:
        """Convert hex color to FFmpeg ASS color format.

        Args:
            hex_color: Hex color string (e.g., "#FFFFFF" or "#FFFFFFCC" with alpha)

        Returns:
            FFmpeg color string in &HAABBGGRR format
        """
        # Remove # prefix
        hex_color = hex_color.lstrip("#")

        # Parse RGBA components
        if len(hex_color) == 6:
            # No alpha, assume fully opaque
            r, g, b = hex_color[0:2], hex_color[2:4], hex_color[4:6]
            a = "FF"
        elif len(hex_color) == 8:
            # With alpha
            r, g, b, a = hex_color[0:2], hex_color[2:4], hex_color[4:6], hex_color[6:8]
        else:
            # Invalid format, use white
            return "&H00FFFFFF"

        # Convert to FFmpeg format: &HAABBGGRR (note: BGR order, not RGB)
        return f"&H{a}{b}{g}{r}".upper()

    async def _copy_video(self, input_path: str, output_path: str) -> None:
        """Copy video without modification.

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
            self.logger.info("Copying video without captions")
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            self.logger.info("Video copy completed successfully")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"FFmpeg copy failed: {e.stderr}")
            raise RuntimeError(f"FFmpeg copy failed: {e.stderr}") from e
