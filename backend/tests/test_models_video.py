"""Tests for Video model."""


import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.video import Video, VideoStatus


@pytest.mark.asyncio
async def test_video_creation_with_required_fields(db_session: AsyncSession):
    """Test Video model creation with required fields."""
    # Create user first
    user = User(email="test@example.com", hashed_password="hashed")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Create video with required fields
    video = Video(
        user_id=user.id,
        title="Test Video",
        status=VideoStatus.UPLOADED,
    )
    db_session.add(video)
    await db_session.commit()
    await db_session.refresh(video)

    assert video.id is not None
    assert video.user_id == user.id
    assert video.title == "Test Video"
    assert video.status == VideoStatus.UPLOADED
    assert video.created_at is not None
    assert video.updated_at is not None


@pytest.mark.asyncio
async def test_video_model_validation_title(db_session: AsyncSession):
    """Test Video model validation for title field."""
    user = User(email="test@example.com", hashed_password="hashed")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Title is required (max_length=255)
    video = Video(
        user_id=user.id,
        title="A" * 255,  # Max length
        status=VideoStatus.UPLOADED,
    )
    db_session.add(video)
    await db_session.commit()
    await db_session.refresh(video)

    assert len(video.title) == 255


@pytest.mark.asyncio
async def test_video_model_status_enum(db_session: AsyncSession):
    """Test Video model status enum values."""
    user = User(email="test@example.com", hashed_password="hashed")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Test all status enum values
    statuses = [
        VideoStatus.UPLOADED,
        VideoStatus.PROCESSING,
        VideoStatus.COMPLETED,
        VideoStatus.FAILED,
    ]

    for status in statuses:
        video = Video(
            user_id=user.id,
            title=f"Test Video {status.value}",
            status=status,
        )
        db_session.add(video)
        await db_session.commit()
        await db_session.refresh(video)

        assert video.status == status


@pytest.mark.asyncio
async def test_video_model_foreign_key_relationship(db_session: AsyncSession):
    """Test Video model foreign key relationship with User."""
    user = User(email="test@example.com", hashed_password="hashed")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    video = Video(
        user_id=user.id,
        title="Test Video",
        status=VideoStatus.UPLOADED,
    )
    db_session.add(video)
    await db_session.commit()
    await db_session.refresh(video)

    # Verify foreign key relationship
    assert video.user_id == user.id

    # Verify user_id is indexed (can't directly test index, but foreign key exists)
    # The relationship is established through the foreign key constraint


@pytest.mark.asyncio
async def test_video_model_metadata_fields(db_session: AsyncSession):
    """Test Video model metadata fields (duration, resolution, format)."""
    user = User(email="test@example.com", hashed_password="hashed")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    video = Video(
        user_id=user.id,
        title="Test Video",
        status=VideoStatus.COMPLETED,
        duration=120.5,  # seconds
        resolution="1920x1080",
        format="mp4",
        file_size=1024 * 1024 * 100,  # 100 MB
    )
    db_session.add(video)
    await db_session.commit()
    await db_session.refresh(video)

    assert video.duration == 120.5
    assert video.resolution == "1920x1080"
    assert video.format == "mp4"
    assert video.file_size == 1024 * 1024 * 100


@pytest.mark.asyncio
async def test_video_model_optional_fields(db_session: AsyncSession):
    """Test Video model optional fields can be None."""
    user = User(email="test@example.com", hashed_password="hashed")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    video = Video(
        user_id=user.id,
        title="Test Video",
        status=VideoStatus.UPLOADED,
        description=None,
        duration=None,
        resolution=None,
        format=None,
        file_size=None,
        s3_key=None,
        cloudfront_url=None,
    )
    db_session.add(video)
    await db_session.commit()
    await db_session.refresh(video)

    assert video.description is None
    assert video.duration is None
    assert video.resolution is None
    assert video.format is None
    assert video.file_size is None
    assert video.s3_key is None
    assert video.cloudfront_url is None


@pytest.mark.asyncio
async def test_video_model_timestamps(db_session: AsyncSession):
    """Test Video model timestamps are automatically set."""
    from datetime import datetime

    user = User(email="test@example.com", hashed_password="hashed")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    video = Video(
        user_id=user.id,
        title="Test Video",
        status=VideoStatus.UPLOADED,
    )
    db_session.add(video)
    await db_session.commit()
    await db_session.refresh(video)

    assert video.created_at is not None
    assert video.updated_at is not None
    # Timestamps should be set and very close (within 1 second)
    assert abs((video.created_at - video.updated_at).total_seconds()) < 1
    # Both should be recent (within last minute)
    now = datetime.utcnow()
    assert abs((now - video.created_at).total_seconds()) < 60
    assert abs((now - video.updated_at).total_seconds()) < 60
