"""Transcription service for OpenAI Whisper API integration."""

import os
import tempfile
from collections.abc import Callable
from typing import Any
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

    async def get_transcript(self, video_id: UUID) -> Transcript | None:
        """Get transcript for a video.

        Args:
            video_id: Video ID

        Returns:
            Transcript if found, None otherwise
        """
        result = await self.db.execute(select(Transcript).where(Transcript.video_id == video_id))
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
        language: str | None = None,
        accuracy_score: float | None = None,
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

        result = await self.db.execute(select(Transcript).where(Transcript.id == transcript_id))
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

    def extract_audio_from_video(self, video_path: str, output_path: str) -> None:
        """Extract audio track from video file.

        Args:
            video_path: Path to video file
            output_path: Path to save extracted audio file
        """
        container = av.open(video_path)
        audio_stream = None

        # Find audio stream
        for stream in container.streams.audio:
            audio_stream = stream
            break

        if not audio_stream:
            raise ValueError("No audio stream found in video")

        # Extract audio
        output_container = av.open(output_path, mode="w")
        output_stream = output_container.add_stream("mp3", rate=16000)

        for frame in container.decode(audio_stream):
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
        self, audio_path: str, language: str | None = None
    ) -> dict[str, Any]:
        """Transcribe audio file using OpenAI Whisper API.

        Args:
            audio_path: Path to audio file
            language: Optional language code hint (ISO 639-1)

        Returns:
            Transcription result with text and word timestamps
        """
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

    async def transcribe_video(
        self, video_id: UUID, update_progress: Callable[[int], None] | None = None
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
                self.extract_audio_from_video(video_path, audio_path)

                # Check file size (Whisper supports up to 25MB)
                file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
                if file_size_mb > 25:
                    # For now, raise error - chunking can be added later
                    raise ValueError(
                        f"Audio file too large ({file_size_mb:.2f}MB). Whisper supports up to 25MB."
                    )

                # Update progress: Transcribing
                if update_progress:
                    update_progress(50)

                # Transcribe audio
                transcription_result = await self.transcribe_audio(
                    audio_path,
                    language=None,  # Auto-detect language
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
            srt_lines.append(f"{format_timestamp(start_time)} --> {format_timestamp(end_time)}")
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
            vtt_lines.append(f"{format_timestamp(start_time)} --> {format_timestamp(end_time)}")
            vtt_lines.append(text)
            vtt_lines.append("")

        return "\n".join(vtt_lines)
