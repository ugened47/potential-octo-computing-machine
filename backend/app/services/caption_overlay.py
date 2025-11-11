"""Caption overlay service for burning captions into video."""

import asyncio
import logging
import os
import tempfile
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class CaptionOverlayService:
    """Service for overlaying captions on video."""

    @staticmethod
    async def overlay_captions(
        input_path: str,
        output_path: str,
        transcript: list[dict],
        caption_style: dict,
    ) -> bool:
        """Overlay captions on video using FFmpeg drawtext filter.

        Args:
            input_path: Path to input video file
            output_path: Path to output video file
            transcript: List of transcript segments with word-level timing
            caption_style: Caption style configuration

        Returns:
            bool: True if overlay succeeded
        """
        try:
            logger.info(f"Overlaying captions: {input_path} -> {output_path}")

            # Generate caption chunks from transcript
            caption_chunks = CaptionOverlayService._generate_caption_chunks(
                transcript, caption_style
            )

            # Create SRT subtitle file
            srt_path = await CaptionOverlayService._create_srt_file(caption_chunks)

            try:
                # Build FFmpeg command with subtitles
                success = await CaptionOverlayService._burn_subtitles(
                    input_path, output_path, srt_path, caption_style
                )

                return success

            finally:
                # Clean up temporary SRT file
                if os.path.exists(srt_path):
                    os.remove(srt_path)

        except Exception as e:
            logger.error(f"Error overlaying captions: {e}")
            return False

    @staticmethod
    def _generate_caption_chunks(
        transcript: list[dict], caption_style: dict
    ) -> list[dict]:
        """Generate caption chunks from transcript.

        Args:
            transcript: List of transcript segments
            caption_style: Caption style configuration

        Returns:
            List of caption chunks with timing and text
        """
        chunks = []
        max_chars_per_line = caption_style.get("max_chars_per_line", 35)
        min_duration = 0.8  # Minimum caption duration in seconds

        current_chunk = {"text": "", "start": None, "end": None, "words": []}

        for segment in transcript:
            # Handle both word-level and segment-level transcripts
            if "words" in segment:
                words = segment["words"]
            else:
                # Segment-level transcript - split into words
                words = [
                    {
                        "word": word,
                        "start": segment["start"],
                        "end": segment["end"],
                    }
                    for word in segment["text"].split()
                ]

            for word_data in words:
                word = word_data.get("word", "").strip()
                if not word:
                    continue

                # Check if adding this word exceeds max characters
                potential_text = (
                    f"{current_chunk['text']} {word}"
                    if current_chunk["text"]
                    else word
                )

                if len(potential_text) > max_chars_per_line and current_chunk["text"]:
                    # Finish current chunk
                    if current_chunk["start"] is not None:
                        # Ensure minimum duration
                        duration = current_chunk["end"] - current_chunk["start"]
                        if duration < min_duration:
                            current_chunk["end"] = current_chunk["start"] + min_duration

                        chunks.append(current_chunk)

                    # Start new chunk
                    current_chunk = {
                        "text": word,
                        "start": word_data.get("start", 0),
                        "end": word_data.get("end", 0),
                        "words": [word],
                    }
                else:
                    # Add word to current chunk
                    if current_chunk["start"] is None:
                        current_chunk["start"] = word_data.get("start", 0)

                    current_chunk["end"] = word_data.get("end", 0)
                    current_chunk["text"] = potential_text
                    current_chunk["words"].append(word)

        # Add final chunk
        if current_chunk["text"] and current_chunk["start"] is not None:
            duration = current_chunk["end"] - current_chunk["start"]
            if duration < min_duration:
                current_chunk["end"] = current_chunk["start"] + min_duration

            chunks.append(current_chunk)

        logger.info(f"Generated {len(chunks)} caption chunks")
        return chunks

    @staticmethod
    async def _create_srt_file(caption_chunks: list[dict]) -> str:
        """Create SRT subtitle file from caption chunks.

        Args:
            caption_chunks: List of caption chunks

        Returns:
            str: Path to created SRT file
        """
        # Create temporary SRT file
        fd, srt_path = tempfile.mkstemp(suffix=".srt", text=True)

        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                for i, chunk in enumerate(caption_chunks, start=1):
                    start_time = CaptionOverlayService._format_srt_time(
                        chunk["start"]
                    )
                    end_time = CaptionOverlayService._format_srt_time(chunk["end"])

                    f.write(f"{i}\n")
                    f.write(f"{start_time} --> {end_time}\n")
                    f.write(f"{chunk['text']}\n")
                    f.write("\n")

            logger.info(f"Created SRT file: {srt_path}")
            return srt_path

        except Exception as e:
            os.close(fd)
            if os.path.exists(srt_path):
                os.remove(srt_path)
            raise e

    @staticmethod
    def _format_srt_time(seconds: float) -> str:
        """Format time in seconds to SRT format (HH:MM:SS,mmm).

        Args:
            seconds: Time in seconds

        Returns:
            str: Formatted time string
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        milliseconds = int((seconds % 1) * 1000)

        return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"

    @staticmethod
    async def _burn_subtitles(
        input_path: str, output_path: str, srt_path: str, caption_style: dict
    ) -> bool:
        """Burn subtitles into video using FFmpeg.

        Args:
            input_path: Input video path
            output_path: Output video path
            srt_path: Path to SRT subtitle file
            caption_style: Caption style configuration

        Returns:
            bool: True if successful
        """
        try:
            # Extract style parameters
            font_family = caption_style.get("font_family", "Arial")
            font_size = caption_style.get("font_size", 24)
            text_color = caption_style.get("text_color", "#FFFFFF")
            background_color = caption_style.get("background_color", "rgba(0,0,0,0.7)")
            stroke_color = caption_style.get("stroke_color", "#000000")
            stroke_width = caption_style.get("stroke_width", 2)
            position = caption_style.get("position", "bottom")
            y_offset = caption_style.get("y_offset", 10)
            alignment = caption_style.get("alignment", "center")

            # Convert hex color to decimal
            if text_color.startswith("#"):
                text_color = f"0x{text_color[1:]}"
            if stroke_color.startswith("#"):
                stroke_color = f"0x{stroke_color[1:]}"

            # Calculate position
            if position == "bottom":
                y_position = f"h-th-{y_offset}"
            elif position == "top":
                y_position = str(y_offset)
            else:  # center
                y_position = "(h-th)/2"

            # Calculate x position based on alignment
            if alignment == "center":
                x_position = "(w-tw)/2"
            elif alignment == "right":
                x_position = "w-tw-10"
            else:  # left
                x_position = "10"

            # Escape the SRT path for FFmpeg
            srt_path_escaped = srt_path.replace("\\", "\\\\").replace(":", "\\:")

            # Build subtitles filter
            # Using subtitles filter with style overrides
            subtitles_filter = f"subtitles='{srt_path_escaped}':force_style='FontName={font_family},FontSize={font_size},PrimaryColour={text_color},OutlineColour={stroke_color},Outline={stroke_width},Alignment=2,MarginV={y_offset}'"

            cmd = [
                "ffmpeg",
                "-i",
                input_path,
                "-vf",
                subtitles_filter,
                "-c:a",
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
                logger.error(f"FFmpeg subtitle burn failed: {stderr.decode()}")
                return False

            logger.info(f"Subtitle burn successful: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Error burning subtitles: {e}")
            return False

    @staticmethod
    def validate_caption_style(caption_style: dict) -> bool:
        """Validate caption style configuration.

        Args:
            caption_style: Caption style configuration

        Returns:
            bool: True if valid

        Raises:
            ValueError: If caption style is invalid
        """
        required_fields = [
            "font_family",
            "font_size",
            "text_color",
            "position",
        ]

        for field in required_fields:
            if field not in caption_style:
                raise ValueError(f"Missing required caption style field: {field}")

        # Validate font size
        font_size = caption_style["font_size"]
        if not isinstance(font_size, (int, float)) or font_size <= 0:
            raise ValueError("font_size must be a positive number")

        # Validate position
        position = caption_style["position"]
        if position not in ["top", "center", "bottom"]:
            raise ValueError("position must be 'top', 'center', or 'bottom'")

        return True
