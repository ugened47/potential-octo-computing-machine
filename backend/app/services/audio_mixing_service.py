"""Audio mixing service for Advanced Editor."""

import asyncio
import os
import subprocess
from pathlib import Path


class AudioMixingService:
    """Service for mixing and processing multiple audio tracks."""

    async def mix_audio_tracks(
        self,
        audio_files: list[dict],
        output_path: str,
    ) -> str:
        """Mix multiple audio tracks into single stereo output.

        Args:
            audio_files: List of dicts with keys:
                - path: Path to audio file
                - start_time: When audio starts on timeline
                - end_time: When audio ends on timeline
                - volume: Volume level (0.0 to 1.0)
                - fade_in: Fade in duration in seconds (optional)
                - fade_out: Fade out duration in seconds (optional)
            output_path: Path to output mixed audio file

        Returns:
            Path to mixed audio file
        """
        if not audio_files:
            raise ValueError("No audio files provided for mixing")

        # Build FFmpeg filter complex for mixing
        inputs = []
        filters = []
        mix_inputs = []

        for idx, audio in enumerate(audio_files):
            inputs.extend(["-i", audio["path"]])

            # Build filter chain for this audio track
            filter_chain = f"[{idx}:a]"

            # Apply volume
            volume = audio.get("volume", 1.0)
            filter_chain += f"volume={volume}"

            # Apply fade in
            if audio.get("fade_in", 0) > 0:
                filter_chain += f",afade=t=in:st=0:d={audio['fade_in']}"

            # Apply fade out
            if audio.get("fade_out", 0) > 0:
                duration = audio["end_time"] - audio["start_time"]
                fade_start = duration - audio["fade_out"]
                filter_chain += f",afade=t=out:st={fade_start}:d={audio['fade_out']}"

            # Apply delay if audio doesn't start at 0
            if audio.get("start_time", 0) > 0:
                delay_ms = int(audio["start_time"] * 1000)
                filter_chain += f",adelay={delay_ms}|{delay_ms}"

            filter_chain += f"[a{idx}]"
            filters.append(filter_chain)
            mix_inputs.append(f"[a{idx}]")

        # Combine all audio streams
        mix_filter = "".join(mix_inputs) + f"amix=inputs={len(audio_files)}:duration=longest[aout]"
        filters.append(mix_filter)

        # Build full FFmpeg command
        cmd = ["ffmpeg", "-y"]
        cmd.extend(inputs)
        cmd.extend(["-filter_complex", ";".join(filters)])
        cmd.extend(["-map", "[aout]", "-ac", "2", "-ar", "48000", output_path])

        # Run FFmpeg
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise RuntimeError(f"FFmpeg audio mixing failed: {stderr.decode()}")

        return output_path

    async def apply_audio_fade(
        self,
        audio_path: str,
        fade_in: float,
        fade_out: float,
        output_path: str,
    ) -> str:
        """Apply fade in/out effects to audio.

        Args:
            audio_path: Path to input audio file
            fade_in: Fade in duration in seconds
            fade_out: Fade out duration in seconds
            output_path: Path to output audio file

        Returns:
            Path to processed audio file
        """
        # Get audio duration first
        probe_cmd = [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            audio_path,
        ]

        process = await asyncio.create_subprocess_exec(
            *probe_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise RuntimeError(f"FFprobe failed: {stderr.decode()}")

        duration = float(stdout.decode().strip())

        # Build filter
        filters = []
        if fade_in > 0:
            filters.append(f"afade=t=in:st=0:d={fade_in}")

        if fade_out > 0:
            fade_start = duration - fade_out
            filters.append(f"afade=t=out:st={fade_start}:d={fade_out}")

        filter_str = ",".join(filters) if filters else "anull"

        # Apply fade
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            audio_path,
            "-af",
            filter_str,
            output_path,
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise RuntimeError(f"FFmpeg fade failed: {stderr.decode()}")

        return output_path

    async def normalize_audio(
        self,
        audio_path: str,
        target_level: float,
        output_path: str,
    ) -> str:
        """Normalize audio to target level.

        Args:
            audio_path: Path to input audio file
            target_level: Target level in LUFS (e.g., -16.0)
            output_path: Path to output audio file

        Returns:
            Path to normalized audio file
        """
        # Use loudnorm filter for normalization
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            audio_path,
            "-af",
            f"loudnorm=I={target_level}:TP=-1.5:LRA=11",
            "-ar",
            "48000",
            output_path,
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise RuntimeError(f"FFmpeg normalization failed: {stderr.decode()}")

        return output_path

    async def extract_audio_from_video(
        self,
        video_path: str,
        output_path: str,
        start: float = 0,
        duration: float | None = None,
    ) -> str:
        """Extract audio track from video file.

        Args:
            video_path: Path to video file
            output_path: Path to output audio file
            start: Start time in seconds
            duration: Duration in seconds (None for entire video)

        Returns:
            Path to extracted audio file
        """
        cmd = ["ffmpeg", "-y"]

        if start > 0:
            cmd.extend(["-ss", str(start)])

        cmd.extend(["-i", video_path])

        if duration is not None:
            cmd.extend(["-t", str(duration)])

        cmd.extend(["-vn", "-acodec", "pcm_s16le", "-ar", "48000", "-ac", "2", output_path])

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise RuntimeError(f"FFmpeg audio extraction failed: {stderr.decode()}")

        return output_path

    def calculate_audio_levels(self, audio_path: str) -> dict:
        """Analyze audio levels (peak, RMS, LUFS).

        Args:
            audio_path: Path to audio file

        Returns:
            Dictionary with audio analysis data
        """
        # Use ffmpeg astats filter
        cmd = [
            "ffmpeg",
            "-i",
            audio_path,
            "-af",
            "astats=metadata=1:reset=1",
            "-f",
            "null",
            "-",
        ]

        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        # Parse output for statistics
        stderr = result.stderr
        levels = {
            "peak_level": 0.0,
            "rms_level": 0.0,
            "duration": 0.0,
        }

        # Simple parsing (in production, use more robust parsing)
        for line in stderr.split("\n"):
            if "lavfi.astats.Overall.Peak_level" in line:
                try:
                    levels["peak_level"] = float(line.split("=")[-1].strip())
                except ValueError:
                    pass
            elif "lavfi.astats.Overall.RMS_level" in line:
                try:
                    levels["rms_level"] = float(line.split("=")[-1].strip())
                except ValueError:
                    pass

        return levels

    async def create_audio_waveform(
        self,
        audio_path: str,
        width: int,
        height: int,
        output_path: str,
    ) -> str:
        """Generate waveform visualization image.

        Args:
            audio_path: Path to audio file
            width: Waveform width in pixels
            height: Waveform height in pixels
            output_path: Path to output PNG file

        Returns:
            Path to waveform PNG
        """
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            audio_path,
            "-filter_complex",
            f"showwavespic=s={width}x{height}:colors=0x4A90E2",
            "-frames:v",
            "1",
            output_path,
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise RuntimeError(f"FFmpeg waveform generation failed: {stderr.decode()}")

        return output_path
