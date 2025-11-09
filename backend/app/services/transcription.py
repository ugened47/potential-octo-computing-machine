"""Transcription service for OpenAI Whisper API integration."""

import io
import json
import os
import tempfile
from typing import Any, Callable, Optional
from uuid import UUID

import av
import boto3
from openai import OpenAI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.config import settings
from app.models.transcript import Transcript, TranscriptStatus
from app.models.video import Video, VideoStatus


class TranscriptionService:
    """Service for handling video transcription."""

    def __init__(self, db: AsyncSession):
        """Initialize transcription service.

        Args:
            db: Database session
        """
        self.db = db
        self.openai_client = OpenAI(api_key=settings.openai_api_key)
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.aws_region,
        )

    async def get_transcript(self, video_id: UUID) -> Optional[Transcript]:
        """Get transcript for a video.

        Args:
            video_id: Video ID

        Returns:
            Transcript if found, None otherwise
        """
        result = await self.db.execute(
            select(Transcript).where(Transcript.video_id == video_id)
        )
        return result.scalar_one_or_none()

    async def create_transcript_record(
        self, video_id: UUID, status: TranscriptStatus = TranscriptStatus.PROCESSING
    ) -> Transcript:
        """Create a new transcript record.

        Args:
            video_id: Video ID
            status: Initial transcript status

        Returns:
            Created transcript record
        """
        transcript = Transcript(
            video_id=video_id,
            full_text="",
            word_timestamps={},
            status=status,
        )
        self.db.add(transcript)
        await self.db.commit()
        await self.db.refresh(transcript)
        return transcript

    async def update_transcript(
        self,
        transcript_id: UUID,
        full_text: str,
        word_timestamps: dict[str, Any],
        language: Optional[str] = None,
        accuracy_score: Optional[float] = None,
        status: TranscriptStatus = TranscriptStatus.COMPLETED,
    ) -> Transcript:
        """Update transcript with transcription results.

        Args:
            transcript_id: Transcript ID
            full_text: Full transcript text
            word_timestamps: Word-level timestamps
            language: Detected language code
            accuracy_score: Optional accuracy score
            status: Transcript status

        Returns:
            Updated transcript
        """
        from datetime import datetime

        result = await self.db.execute(
            select(Transcript).where(Transcript.id == transcript_id)
        )
        transcript = result.scalar_one_or_none()

        if not transcript:
            raise ValueError(f"Transcript {transcript_id} not found")

        transcript.full_text = full_text
        transcript.word_timestamps = word_timestamps
        transcript.language = language
        transcript.accuracy_score = accuracy_score
        transcript.status = status
        transcript.updated_at = datetime.utcnow()

        if status == TranscriptStatus.COMPLETED:
            transcript.completed_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(transcript)
        return transcript

    def extract_audio_from_video(
        self, video_path: str, output_path: str, convert_to_mono: bool = True
    ) -> None:
        """Extract audio track from video file.

        Args:
            video_path: Path to video file
            output_path: Path to save extracted audio file
            convert_to_mono: Convert stereo to mono for cost optimization (default: True)
        """
        container = av.open(video_path)
        audio_stream = None

        # Find audio stream
        for stream in container.streams.audio:
            audio_stream = stream
            break

        if not audio_stream:
            raise ValueError("No audio stream found in video")

        # Extract audio - optimize for Whisper API
        output_container = av.open(output_path, mode="w")

        # Use mono to reduce costs by ~50%
        # Whisper charges per minute of audio, stereo = 2x cost
        if convert_to_mono:
            output_stream = output_container.add_stream("mp3", rate=16000)
            output_stream.channels = 1  # Force mono
        else:
            output_stream = output_container.add_stream("mp3", rate=16000)

        for frame in container.decode(audio_stream):
            # Convert stereo to mono if needed
            if convert_to_mono and frame.layout.channels > 1:
                frame = frame.reformat(layout="mono")

            frame.pts = None
            for packet in output_stream.encode(frame):
                output_container.mux(packet)

        # Flush remaining packets
        for packet in output_stream.encode():
            output_container.mux(packet)

        output_container.close()
        container.close()

    def download_video_from_s3(self, s3_key: str, local_path: str) -> None:
        """Download video file from S3.

        Args:
            s3_key: S3 object key
            local_path: Local path to save the file
        """
        self.s3_client.download_file(settings.s3_bucket, s3_key, local_path)

    async def transcribe_audio(
        self, audio_path: str, language: Optional[str] = None, max_retries: int = 4
    ) -> dict[str, Any]:
        """Transcribe audio file using OpenAI Whisper API with retry logic.

        Args:
            audio_path: Path to audio file
            language: Optional language code hint (ISO 639-1)
            max_retries: Maximum number of retry attempts (default: 4)

        Returns:
            Transcription result with text and word timestamps

        Raises:
            Exception: If transcription fails after all retries
        """
        import time
        from openai import APIError, APIConnectionError, RateLimitError

        last_error = None

        for attempt in range(max_retries + 1):
            try:
                with open(audio_path, "rb") as audio_file:
                    transcript_response = self.openai_client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        response_format="verbose_json",
                        timestamp_granularities=["word"],
                        language=language,
                    )

                # Extract word timestamps from response
                word_timestamps = {
                    "words": [
                        {
                            "word": word["word"],
                            "start": word["start"],
                            "end": word["end"],
                            "confidence": getattr(word, "probability", None),
                        }
                        for word in transcript_response.words
                    ]
                }

                return {
                    "text": transcript_response.text,
                    "language": transcript_response.language,
                    "word_timestamps": word_timestamps,
                }

            except (APIError, APIConnectionError, RateLimitError) as e:
                last_error = e

                # Don't retry on client errors (400)
                if hasattr(e, "status_code") and e.status_code == 400:
                    raise

                # If we've exhausted retries, raise the error
                if attempt >= max_retries:
                    break

                # Exponential backoff: 1s, 2s, 4s, 8s
                wait_time = 2**attempt
                time.sleep(wait_time)

                continue

            except Exception as e:
                # Don't retry on unexpected errors
                raise

        # If we get here, all retries failed
        raise Exception(f"Transcription failed after {max_retries + 1} attempts") from last_error

    def split_audio_file(
        self, audio_path: str, chunk_size_mb: int = 20
    ) -> list[tuple[str, float]]:
        """Split audio file into chunks if larger than chunk_size_mb.

        Args:
            audio_path: Path to audio file
            chunk_size_mb: Maximum chunk size in MB (default: 20)

        Returns:
            List of tuples (chunk_path, start_offset_seconds)
        """
        # Check file size
        file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)

        if file_size_mb <= chunk_size_mb:
            # File is small enough, return as single chunk
            return [(audio_path, 0.0)]

        # Split into chunks
        chunks = []
        container = av.open(audio_path)

        # Get audio stream
        audio_stream = None
        for stream in container.streams.audio:
            audio_stream = stream
            break

        if not audio_stream:
            raise ValueError("No audio stream found")

        # Calculate chunk duration based on file size and bitrate
        # Target: chunk_size_mb per chunk
        total_duration = container.duration / av.time_base if container.duration else 0
        num_chunks = int(file_size_mb / chunk_size_mb) + 1
        chunk_duration = total_duration / num_chunks

        current_time = 0.0
        chunk_index = 0

        while current_time < total_duration:
            # Create chunk file
            chunk_path = tempfile.NamedTemporaryFile(
                delete=False, suffix=f"_chunk_{chunk_index}.mp3"
            ).name

            # Open output container
            output_container = av.open(chunk_path, mode="w")
            output_stream = output_container.add_stream("mp3", rate=16000)
            output_stream.channels = 1  # Mono

            # Seek to start time
            container.seek(int(current_time * av.time_base))

            end_time = min(current_time + chunk_duration, total_duration)

            # Write frames for this chunk
            for frame in container.decode(audio_stream):
                if frame.time < current_time:
                    continue
                if frame.time >= end_time:
                    break

                # Convert to mono
                if frame.layout.channels > 1:
                    frame = frame.reformat(layout="mono")

                frame.pts = None
                for packet in output_stream.encode(frame):
                    output_container.mux(packet)

            # Flush
            for packet in output_stream.encode():
                output_container.mux(packet)

            output_container.close()

            chunks.append((chunk_path, current_time))
            current_time = end_time
            chunk_index += 1

        container.close()

        return chunks

    async def transcribe_audio_chunked(
        self, audio_path: str, language: Optional[str] = None, chunk_size_mb: int = 20
    ) -> dict[str, Any]:
        """Transcribe audio file with chunking for large files.

        Args:
            audio_path: Path to audio file
            language: Optional language code hint
            chunk_size_mb: Maximum chunk size in MB (default: 20)

        Returns:
            Combined transcription result
        """
        # Split into chunks if needed
        chunks = self.split_audio_file(audio_path, chunk_size_mb)

        if len(chunks) == 1:
            # Single chunk, use normal transcription
            return await self.transcribe_audio(audio_path, language)

        # Transcribe each chunk and merge results
        full_text_parts = []
        all_words = []

        for chunk_path, time_offset in chunks:
            try:
                # Transcribe chunk
                chunk_result = await self.transcribe_audio(chunk_path, language)

                # Add text
                full_text_parts.append(chunk_result["text"])

                # Add words with time offset
                for word in chunk_result["word_timestamps"]["words"]:
                    word_with_offset = {
                        "word": word["word"],
                        "start": word["start"] + time_offset,
                        "end": word["end"] + time_offset,
                        "confidence": word["confidence"],
                    }
                    all_words.append(word_with_offset)

            finally:
                # Clean up chunk file (unless it's the original file)
                if chunk_path != audio_path and os.path.exists(chunk_path):
                    os.unlink(chunk_path)

        return {
            "text": " ".join(full_text_parts),
            "language": language or "en",  # Use detected language from first chunk
            "word_timestamps": {"words": all_words},
        }

    async def transcribe_video(
        self, video_id: UUID, update_progress: Optional[Callable[[int], None]] = None
    ) -> Transcript:
        """Transcribe a video (full workflow).

        Args:
            video_id: Video ID
            update_progress: Optional callback to update progress (progress: int)

        Returns:
            Created/updated transcript
        """
        # Get video
        result = await self.db.execute(select(Video).where(Video.id == video_id))
        video = result.scalar_one_or_none()

        if not video:
            raise ValueError(f"Video {video_id} not found")

        if not video.s3_key:
            raise ValueError(f"Video {video_id} has no S3 key")

        # Check if transcript already exists
        transcript = await self.get_transcript(video_id)
        if not transcript:
            transcript = await self.create_transcript_record(video_id)

        # Update progress: Downloading
        if update_progress:
            update_progress(10)

        # Download video from S3
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as video_file:
            video_path = video_file.name

        try:
            self.download_video_from_s3(video.s3_key, video_path)

            # Update progress: Extracting audio
            if update_progress:
                update_progress(30)

            # Extract audio
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as audio_file:
                audio_path = audio_file.name

            try:
                self.extract_audio_from_video(video_path, audio_path, convert_to_mono=True)

                # Update progress: Transcribing
                if update_progress:
                    update_progress(50)

                # Transcribe audio with automatic chunking for large files
                transcription_result = await self.transcribe_audio_chunked(
                    audio_path, language=None, chunk_size_mb=20
                )

                # Update progress: Saving
                if update_progress:
                    update_progress(90)

                # Update transcript record
                transcript = await self.update_transcript(
                    transcript_id=transcript.id,
                    full_text=transcription_result["text"],
                    word_timestamps=transcription_result["word_timestamps"],
                    language=transcription_result["language"],
                    status=TranscriptStatus.COMPLETED,
                )

                # Update video status
                video.status = VideoStatus.COMPLETED
                await self.db.commit()

                # Update progress: Complete
                if update_progress:
                    update_progress(100)

                return transcript

            finally:
                # Clean up audio file
                if os.path.exists(audio_path):
                    os.unlink(audio_path)

        finally:
            # Clean up video file
            if os.path.exists(video_path):
                os.unlink(video_path)

    def format_transcript_srt(self, transcript: Transcript) -> str:
        """Format transcript as SRT (SubRip) subtitle file.

        Args:
            transcript: Transcript to format

        Returns:
            SRT formatted string
        """
        if not transcript.word_timestamps.get("words"):
            return ""

        srt_lines = []
        words = transcript.word_timestamps["words"]

        # Group words into sentences/phrases (simple grouping by time gaps)
        segments = []
        current_segment = []

        for i, word_data in enumerate(words):
            if not current_segment:
                current_segment.append(word_data)
            else:
                # If gap > 1 second, start new segment
                last_end = current_segment[-1]["end"]
                if word_data["start"] - last_end > 1.0:
                    segments.append(current_segment)
                    current_segment = [word_data]
                else:
                    current_segment.append(word_data)

        if current_segment:
            segments.append(current_segment)

        # Format each segment
        for idx, segment in enumerate(segments, start=1):
            start_time = segment[0]["start"]
            end_time = segment[-1]["end"]

            # Format timestamps (HH:MM:SS,mmm)
            def format_timestamp(seconds: float) -> str:
                hours = int(seconds // 3600)
                minutes = int((seconds % 3600) // 60)
                secs = int(seconds % 60)
                millis = int((seconds % 1) * 1000)
                return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

            text = " ".join(word["word"] for word in segment)
            srt_lines.append(f"{idx}")
            srt_lines.append(
                f"{format_timestamp(start_time)} --> {format_timestamp(end_time)}"
            )
            srt_lines.append(text)
            srt_lines.append("")

        return "\n".join(srt_lines)

    def format_transcript_vtt(self, transcript: Transcript) -> str:
        """Format transcript as VTT (WebVTT) subtitle file.

        Args:
            transcript: Transcript to format

        Returns:
            VTT formatted string
        """
        if not transcript.word_timestamps.get("words"):
            return "WEBVTT\n\n"

        vtt_lines = ["WEBVTT", ""]
        words = transcript.word_timestamps["words"]

        # Group words into segments (similar to SRT)
        segments = []
        current_segment = []

        for word_data in words:
            if not current_segment:
                current_segment.append(word_data)
            else:
                last_end = current_segment[-1]["end"]
                if word_data["start"] - last_end > 1.0:
                    segments.append(current_segment)
                    current_segment = [word_data]
                else:
                    current_segment.append(word_data)

        if current_segment:
            segments.append(current_segment)

        # Format each segment
        for segment in segments:
            start_time = segment[0]["start"]
            end_time = segment[-1]["end"]

            # Format timestamps (HH:MM:SS.mmm)
            def format_timestamp(seconds: float) -> str:
                hours = int(seconds // 3600)
                minutes = int((seconds % 3600) // 60)
                secs = int(seconds % 60)
                millis = int((seconds % 1) * 1000)
                return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"

            text = " ".join(word["word"] for word in segment)
            vtt_lines.append(
                f"{format_timestamp(start_time)} --> {format_timestamp(end_time)}"
            )
            vtt_lines.append(text)
            vtt_lines.append("")

        return "\n".join(vtt_lines)

