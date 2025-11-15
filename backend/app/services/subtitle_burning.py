"""Subtitle burning service for generating and burning subtitles into videos."""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subtitle import SubtitleStyle
from app.models.transcript import Transcript
from app.models.video import Video


class SubtitleBurningService:
    """Service for subtitle burning operations using FFmpeg."""

    def __init__(self, db: AsyncSession):
        """Initialize subtitle burning service."""
        self.db = db

    async def burn_subtitles(
        self, video_id: UUID, language: str, output_format: str = "mp4"
    ) -> str:
        """Burn subtitles into video and return output path."""
        # Get video
        result = await self.db.execute(
            select(Video).where(Video.id == video_id)
        )
        video = result.scalar_one_or_none()
        if not video:
            raise ValueError(f"Video {video_id} not found")

        # Get subtitle style
        result = await self.db.execute(
            select(SubtitleStyle).where(
                SubtitleStyle.video_id == video_id,
                SubtitleStyle.language_code == language,
            )
        )
        style = result.scalar_one_or_none()
        if not style:
            raise ValueError(f"Subtitle style for language '{language}' not found")

        # Get transcript
        result = await self.db.execute(
            select(Transcript).where(Transcript.video_id == video_id)
        )
        transcript = result.scalar_one_or_none()
        if not transcript:
            raise ValueError(f"Transcript for video {video_id} not found")

        # Generate ASS subtitle file
        subtitle_path = await self.generate_ass_subtitle_file(
            video_id, style, language, transcript
        )

        # TODO: Download video from S3 (placeholder for now)
        video_path = f"/tmp/input_{video_id}.mp4"
        output_path = f"/tmp/output_{video_id}_{language}.{output_format}"

        # Apply FFmpeg subtitle burn
        await self.apply_ffmpeg_subtitle_burn(
            video_path, subtitle_path, output_path, style
        )

        # TODO: Upload to S3 and return URL
        return output_path

    async def generate_ass_subtitle_file(
        self,
        video_id: UUID,
        style: SubtitleStyle,
        language: str,
        transcript: Transcript,
    ) -> str:
        """Generate ASS (Advanced SubStation Alpha) subtitle file."""
        # Create temp file
        temp_file = tempfile.NamedTemporaryFile(
            mode="w", suffix=".ass", delete=False, encoding="utf-8"
        )

        # Convert position to ASS alignment (numpad layout: 1-9)
        alignment = self._get_ass_alignment(
            style.position_vertical.value, style.position_horizontal.value
        )

        # Convert hex colors to ASS format (&HAABBGGRR)
        primary_color = self._hex_to_ass_color(style.font_color, style.font_alpha)
        outline_color = self._hex_to_ass_color(
            style.outline_color if style.outline_enabled else "#00000000", 1.0
        )
        back_color = self._hex_to_ass_color(
            style.background_color if style.background_enabled else "#00000000",
            style.background_alpha if style.background_enabled else 0.0,
        )

        # Write ASS header
        temp_file.write("[Script Info]\n")
        temp_file.write("Title: Video Subtitles\n")
        temp_file.write("ScriptType: v4.00+\n")
        temp_file.write("WrapStyle: 0\n")
        temp_file.write("PlayResX: 1920\n")
        temp_file.write("PlayResY: 1080\n\n")

        # Write style definition
        temp_file.write("[V4+ Styles]\n")
        temp_file.write(
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
            "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
            "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
            "Alignment, MarginL, MarginR, MarginV, Encoding\n"
        )

        bold = -1 if style.font_weight.value == "bold" else 0
        outline_width = style.outline_width if style.outline_enabled else 0

        temp_file.write(
            f"Style: Default,{style.font_family},{style.font_size},"
            f"{primary_color},{primary_color},{outline_color},{back_color},"
            f"{bold},0,0,0,100,100,0,0,1,{outline_width},0,"
            f"{alignment},{style.margin_horizontal},{style.margin_horizontal},"
            f"{style.margin_vertical},1\n\n"
        )

        # Write events (dialogue)
        temp_file.write("[Events]\n")
        temp_file.write("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")

        # Generate subtitle segments from transcript
        segments = self._generate_subtitle_segments(
            transcript, style.words_per_line, style.max_lines
        )

        for segment in segments:
            start_time = self._format_ass_time(segment["start_time"])
            end_time = self._format_ass_time(segment["end_time"])
            text = segment["text"]

            temp_file.write(
                f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{text}\n"
            )

        temp_file.close()
        return temp_file.name

    async def generate_srt_subtitle_file(
        self, video_id: UUID, language: str
    ) -> str:
        """Generate SRT (SubRip) subtitle file."""
        # Get transcript
        result = await self.db.execute(
            select(Transcript).where(Transcript.video_id == video_id)
        )
        transcript = result.scalar_one_or_none()
        if not transcript:
            raise ValueError(f"Transcript for video {video_id} not found")

        # Get style for timing parameters
        result = await self.db.execute(
            select(SubtitleStyle).where(
                SubtitleStyle.video_id == video_id,
                SubtitleStyle.language_code == language,
            )
        )
        style = result.scalar_one_or_none()

        words_per_line = style.words_per_line if style else 7
        max_lines = style.max_lines if style else 2

        # Create temp file
        temp_file = tempfile.NamedTemporaryFile(
            mode="w", suffix=".srt", delete=False, encoding="utf-8"
        )

        # Generate segments
        segments = self._generate_subtitle_segments(transcript, words_per_line, max_lines)

        # Write SRT format
        for i, segment in enumerate(segments, start=1):
            start_time = self._format_srt_time(segment["start_time"])
            end_time = self._format_srt_time(segment["end_time"])
            text = segment["text"]

            temp_file.write(f"{i}\n")
            temp_file.write(f"{start_time} --> {end_time}\n")
            temp_file.write(f"{text}\n\n")

        temp_file.close()
        return temp_file.name

    async def apply_ffmpeg_subtitle_burn(
        self, video_path: str, subtitle_path: str, output_path: str, style: SubtitleStyle
    ) -> None:
        """Use FFmpeg to burn subtitles into video."""
        # Check FFmpeg is available
        try:
            subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                check=True,
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise RuntimeError("FFmpeg is not installed or not accessible")

        # Build FFmpeg command
        if subtitle_path.endswith(".ass"):
            # Use ass filter for ASS files
            cmd = [
                "ffmpeg",
                "-i", video_path,
                "-vf", f"ass={subtitle_path}",
                "-c:a", "copy",  # Copy audio without re-encoding
                "-y",  # Overwrite output file
                output_path,
            ]
        else:
            # Use subtitles filter for SRT files
            cmd = [
                "ffmpeg",
                "-i", video_path,
                "-vf", f"subtitles={subtitle_path}",
                "-c:a", "copy",
                "-y",
                output_path,
            ]

        # Execute FFmpeg
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"FFmpeg failed: {e.stderr}")

    def estimate_burn_duration(self, video_duration: float, resolution: str) -> float:
        """Estimate processing time based on video length and resolution."""
        # Basic estimation: ~1x realtime for 1080p, faster for lower resolutions
        base_time = video_duration

        if "1080" in resolution or "1920" in resolution:
            multiplier = 1.0
        elif "720" in resolution or "1280" in resolution:
            multiplier = 0.7
        elif "480" in resolution:
            multiplier = 0.5
        else:
            multiplier = 1.2  # 4K or higher

        return base_time * multiplier

    def validate_subtitle_file(self, subtitle_path: str, format: str) -> bool:
        """Validate ASS or SRT file format."""
        if not os.path.exists(subtitle_path):
            return False

        try:
            with open(subtitle_path, "r", encoding="utf-8") as f:
                content = f.read(1000)  # Read first 1000 chars

                if format == "ass":
                    return "[Script Info]" in content and "[V4+ Styles]" in content
                elif format == "srt":
                    # Basic SRT validation (has numbers and -->)
                    return "-->" in content and any(char.isdigit() for char in content)

        except Exception:
            return False

        return False

    def _generate_subtitle_segments(
        self, transcript: Transcript, words_per_line: int, max_lines: int
    ) -> list[dict[str, Any]]:
        """Generate subtitle segments from transcript word timestamps."""
        # Parse word timestamps from transcript
        word_data = transcript.word_timestamps.get("words", [])
        if not word_data:
            # Fallback: split full text
            words = transcript.full_text.split()
            word_data = [
                {"word": word, "start": i * 0.5, "end": (i + 1) * 0.5}
                for i, word in enumerate(words)
            ]

        segments = []
        current_words = []
        current_start = None

        for word_info in word_data:
            word = word_info.get("word", "")
            start = word_info.get("start", 0.0)
            end = word_info.get("end", 0.0)

            if current_start is None:
                current_start = start

            current_words.append(word)

            # Create segment when we hit words_per_line limit
            if len(current_words) >= words_per_line:
                segments.append({
                    "start_time": current_start,
                    "end_time": end,
                    "text": " ".join(current_words),
                })
                current_words = []
                current_start = None

        # Add remaining words
        if current_words and current_start is not None:
            last_end = word_data[-1].get("end", current_start + 1.0)
            segments.append({
                "start_time": current_start,
                "end_time": last_end,
                "text": " ".join(current_words),
            })

        return segments

    @staticmethod
    def _get_ass_alignment(vertical: str, horizontal: str) -> int:
        """Convert position to ASS alignment code (numpad layout)."""
        alignment_map = {
            ("bottom", "left"): 1,
            ("bottom", "center"): 2,
            ("bottom", "right"): 3,
            ("center", "left"): 4,
            ("center", "center"): 5,
            ("center", "right"): 6,
            ("top", "left"): 7,
            ("top", "center"): 8,
            ("top", "right"): 9,
        }
        return alignment_map.get((vertical, horizontal), 2)  # Default to bottom-center

    @staticmethod
    def _hex_to_ass_color(hex_color: str, alpha: float = 1.0) -> str:
        """Convert hex color to ASS format (&HAABBGGRR)."""
        hex_color = hex_color.lstrip("#")

        # Parse RGB
        if len(hex_color) >= 6:
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
        else:
            r, g, b = 255, 255, 255

        # Convert alpha (0.0-1.0) to hex (00-FF, inverted for ASS)
        a = int((1.0 - alpha) * 255)

        return f"&H{a:02X}{b:02X}{g:02X}{r:02X}"

    @staticmethod
    def _format_ass_time(seconds: float) -> str:
        """Format time for ASS format (H:MM:SS.CC)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centiseconds = int((seconds % 1) * 100)
        return f"{hours}:{minutes:02d}:{secs:02d}.{centiseconds:02d}"

    @staticmethod
    def _format_srt_time(seconds: float) -> str:
        """Format time for SRT format (HH:MM:SS,mmm)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        milliseconds = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"
