"""Tests for Transcript model."""


import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transcript import Transcript, TranscriptStatus
from app.models.user import User
from app.models.video import Video, VideoStatus


@pytest.mark.asyncio
async def test_transcript_creation_with_required_fields(db_session: AsyncSession):
    """Test Transcript model creation with required fields."""
    # Create a user first
    user = User(
        email="test@example.com",
        hashed_password="hashed_password",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Create a video
    video = Video(
        user_id=user.id,
        title="Test Video",
        status=VideoStatus.UPLOADED,
    )
    db_session.add(video)
    await db_session.commit()
    await db_session.refresh(video)

    # Create transcript
    transcript = Transcript(
        video_id=video.id,
        full_text="This is a test transcript.",
        word_timestamps={"words": []},
        status=TranscriptStatus.PROCESSING,
    )
    db_session.add(transcript)
    await db_session.commit()
    await db_session.refresh(transcript)

    assert transcript.id is not None
    assert transcript.video_id == video.id
    assert transcript.full_text == "This is a test transcript."
    assert transcript.status == TranscriptStatus.PROCESSING
    assert transcript.created_at is not None
    assert transcript.updated_at is not None


@pytest.mark.asyncio
async def test_transcript_with_word_timestamps(db_session: AsyncSession):
    """Test Transcript model with word-level timestamps."""
    # Create user and video
    user = User(email="test@example.com", hashed_password="hashed")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    video = Video(user_id=user.id, title="Test", status=VideoStatus.UPLOADED)
    db_session.add(video)
    await db_session.commit()
    await db_session.refresh(video)

    # Create transcript with word timestamps
    word_timestamps = {
        "words": [
            {"word": "Hello", "start": 0.0, "end": 0.5, "confidence": 0.95},
            {"word": "world", "start": 0.5, "end": 1.0, "confidence": 0.92},
        ]
    }
    transcript = Transcript(
        video_id=video.id,
        full_text="Hello world",
        word_timestamps=word_timestamps,
        language="en",
        status=TranscriptStatus.COMPLETED,
    )
    db_session.add(transcript)
    await db_session.commit()
    await db_session.refresh(transcript)

    assert transcript.word_timestamps == word_timestamps
    assert transcript.language == "en"
    assert transcript.status == TranscriptStatus.COMPLETED
    assert len(transcript.word_timestamps["words"]) == 2


@pytest.mark.asyncio
async def test_transcript_status_enum(db_session: AsyncSession):
    """Test Transcript status enum values."""
    user = User(email="test@example.com", hashed_password="hashed")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    video = Video(user_id=user.id, title="Test", status=VideoStatus.UPLOADED)
    db_session.add(video)
    await db_session.commit()
    await db_session.refresh(video)

    # Test PROCESSING status
    transcript1 = Transcript(
        video_id=video.id,
        full_text="Processing",
        status=TranscriptStatus.PROCESSING,
    )
    assert transcript1.status == TranscriptStatus.PROCESSING

    # Test COMPLETED status
    transcript2 = Transcript(
        video_id=video.id,
        full_text="Completed",
        status=TranscriptStatus.COMPLETED,
    )
    assert transcript2.status == TranscriptStatus.COMPLETED

    # Test FAILED status
    transcript3 = Transcript(
        video_id=video.id,
        full_text="Failed",
        status=TranscriptStatus.FAILED,
    )
    assert transcript3.status == TranscriptStatus.FAILED


@pytest.mark.asyncio
async def test_transcript_optional_fields(db_session: AsyncSession):
    """Test Transcript model with optional fields."""
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
        full_text="Test transcript",
        language="en",
        accuracy_score=0.95,
        status=TranscriptStatus.COMPLETED,
    )
    db_session.add(transcript)
    await db_session.commit()
    await db_session.refresh(transcript)

    assert transcript.language == "en"
    assert transcript.accuracy_score == 0.95
    assert transcript.completed_at is None  # Not set initially


@pytest.mark.asyncio
async def test_transcript_video_relationship(db_session: AsyncSession):
    """Test Transcript belongs_to Video relationship."""
    user = User(email="test@example.com", hashed_password="hashed")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    video = Video(user_id=user.id, title="Test Video", status=VideoStatus.UPLOADED)
    db_session.add(video)
    await db_session.commit()
    await db_session.refresh(video)

    transcript = Transcript(
        video_id=video.id,
        full_text="Test",
        status=TranscriptStatus.PROCESSING,
    )
    db_session.add(transcript)
    await db_session.commit()
    await db_session.refresh(transcript)

    # Verify foreign key relationship
    assert transcript.video_id == video.id
