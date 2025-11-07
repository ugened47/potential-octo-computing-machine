"""Tests for transcription service."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4
from unittest.mock import Mock, patch, AsyncMock

from app.models.transcript import Transcript, TranscriptStatus
from app.models.user import User
from app.models.video import Video, VideoStatus
from app.services.transcription import TranscriptionService


@pytest.mark.asyncio
async def test_get_transcript_existing(db_session: AsyncSession):
    """Test getting an existing transcript."""
    # Create user and video
    user = User(email="test@example.com", hashed_password="hashed")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    video = Video(user_id=user.id, title="Test", status=VideoStatus.UPLOADED)
    db_session.add(video)
    await db_session.commit()
    await db_session.refresh(video)

    # Create transcript
    transcript = Transcript(
        video_id=video.id,
        full_text="Test transcript",
        word_timestamps={},
        status=TranscriptStatus.COMPLETED,
    )
    db_session.add(transcript)
    await db_session.commit()
    await db_session.refresh(transcript)

    # Get transcript
    service = TranscriptionService(db_session)
    result = await service.get_transcript(video.id)

    assert result is not None
    assert result.id == transcript.id
    assert result.full_text == "Test transcript"


@pytest.mark.asyncio
async def test_get_transcript_not_found(db_session: AsyncSession):
    """Test getting transcript when it doesn't exist."""
    user = User(email="test@example.com", hashed_password="hashed")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    video = Video(user_id=user.id, title="Test", status=VideoStatus.UPLOADED)
    db_session.add(video)
    await db_session.commit()
    await db_session.refresh(video)

    service = TranscriptionService(db_session)
    result = await service.get_transcript(video.id)

    assert result is None


@pytest.mark.asyncio
async def test_create_transcript_record(db_session: AsyncSession):
    """Test creating a new transcript record."""
    user = User(email="test@example.com", hashed_password="hashed")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    video = Video(user_id=user.id, title="Test", status=VideoStatus.UPLOADED)
    db_session.add(video)
    await db_session.commit()
    await db_session.refresh(video)

    service = TranscriptionService(db_session)
    transcript = await service.create_transcript_record(video.id)

    assert transcript.id is not None
    assert transcript.video_id == video.id
    assert transcript.status == TranscriptStatus.PROCESSING
    assert transcript.full_text == ""


@pytest.mark.asyncio
async def test_update_transcript(db_session: AsyncSession):
    """Test updating transcript with transcription results."""
    user = User(email="test@example.com", hashed_password="hashed")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    video = Video(user_id=user.id, title="Test", status=VideoStatus.UPLOADED)
    db_session.add(video)
    await db_session.commit()
    await db_session.refresh(video)

    transcript = Transcript(
        video_id=video.id,
        full_text="",
        word_timestamps={},
        status=TranscriptStatus.PROCESSING,
    )
    db_session.add(transcript)
    await db_session.commit()
    await db_session.refresh(transcript)

    word_timestamps = {
        "words": [
            {"word": "Hello", "start": 0.0, "end": 0.5, "confidence": 0.95}
        ]
    }

    service = TranscriptionService(db_session)
    updated = await service.update_transcript(
        transcript.id,
        full_text="Hello",
        word_timestamps=word_timestamps,
        language="en",
        status=TranscriptStatus.COMPLETED,
    )

    assert updated.full_text == "Hello"
    assert updated.language == "en"
    assert updated.status == TranscriptStatus.COMPLETED
    assert updated.completed_at is not None


@pytest.mark.asyncio
async def test_format_transcript_srt(db_session: AsyncSession):
    """Test formatting transcript as SRT."""
    user = User(email="test@example.com", hashed_password="hashed")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    video = Video(user_id=user.id, title="Test", status=VideoStatus.UPLOADED)
    db_session.add(video)
    await db_session.commit()
    await db_session.refresh(video)

    transcript = Transcript(
        video_id=video.id,
        full_text="Hello world",
        word_timestamps={
            "words": [
                {"word": "Hello", "start": 0.0, "end": 0.5, "confidence": 0.95},
                {"word": "world", "start": 0.5, "end": 1.0, "confidence": 0.92},
            ]
        },
        status=TranscriptStatus.COMPLETED,
    )

    service = TranscriptionService(db_session)
    srt_content = service.format_transcript_srt(transcript)

    assert "1" in srt_content  # Sequence number
    assert "00:00:00" in srt_content  # Timestamp format
    assert "Hello world" in srt_content


@pytest.mark.asyncio
async def test_format_transcript_vtt(db_session: AsyncSession):
    """Test formatting transcript as VTT."""
    user = User(email="test@example.com", hashed_password="hashed")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    video = Video(user_id=user.id, title="Test", status=VideoStatus.UPLOADED)
    db_session.add(video)
    await db_session.commit()
    await db_session.refresh(video)

    transcript = Transcript(
        video_id=video.id,
        full_text="Hello world",
        word_timestamps={
            "words": [
                {"word": "Hello", "start": 0.0, "end": 0.5, "confidence": 0.95},
                {"word": "world", "start": 0.5, "end": 1.0, "confidence": 0.92},
            ]
        },
        status=TranscriptStatus.COMPLETED,
    )

    service = TranscriptionService(db_session)
    vtt_content = service.format_transcript_vtt(transcript)

    assert "WEBVTT" in vtt_content
    assert "00:00:00" in vtt_content
    assert "Hello world" in vtt_content


@pytest.mark.asyncio
async def test_transcribe_video_missing_s3_key(db_session: AsyncSession):
    """Test transcribe_video raises error when video has no S3 key."""
    user = User(email="test@example.com", hashed_password="hashed")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    video = Video(
        user_id=user.id, title="Test", status=VideoStatus.UPLOADED, s3_key=None
    )
    db_session.add(video)
    await db_session.commit()
    await db_session.refresh(video)

    service = TranscriptionService(db_session)

    with pytest.raises(ValueError, match="no S3 key"):
        await service.transcribe_video(video.id)

