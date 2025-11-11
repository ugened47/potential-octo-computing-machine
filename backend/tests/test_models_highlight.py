"""Tests for Highlight model."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.highlight import Highlight, HighlightStatus, HighlightType
from app.models.user import User
from app.models.video import Video, VideoStatus


@pytest.mark.asyncio
async def test_highlight_creation_with_required_fields(db_session: AsyncSession):
    """Test Highlight model creation with required fields."""
    # Create user first
    user = User(email="test@example.com", hashed_password="hashed")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Create video
    video = Video(
        user_id=user.id,
        title="Test Video",
        status=VideoStatus.UPLOADED,
    )
    db_session.add(video)
    await db_session.commit()
    await db_session.refresh(video)

    # Create highlight with required fields
    highlight = Highlight(
        video_id=video.id,
        start_time=10.5,
        end_time=20.3,
        overall_score=85,
        audio_energy_score=90,
        scene_change_score=75,
        speech_density_score=80,
        keyword_score=85,
        rank=1,
        highlight_type=HighlightType.HIGH_ENERGY,
    )
    db_session.add(highlight)
    await db_session.commit()
    await db_session.refresh(highlight)

    assert highlight.id is not None
    assert highlight.video_id == video.id
    assert highlight.start_time == 10.5
    assert highlight.end_time == 20.3
    assert highlight.overall_score == 85
    assert highlight.audio_energy_score == 90
    assert highlight.scene_change_score == 75
    assert highlight.speech_density_score == 80
    assert highlight.keyword_score == 85
    assert highlight.rank == 1
    assert highlight.highlight_type == HighlightType.HIGH_ENERGY
    assert highlight.status == HighlightStatus.DETECTED  # Default value
    assert highlight.created_at is not None
    assert highlight.updated_at is not None


@pytest.mark.asyncio
async def test_highlight_model_validation_video_id_foreign_key(
    db_session: AsyncSession,
):
    """Test Highlight model video_id foreign key validation."""
    from uuid import uuid4

    # Try to create highlight with non-existent video_id
    from sqlalchemy.exc import IntegrityError

    highlight = Highlight(
        video_id=uuid4(),  # Non-existent video
        start_time=10.0,
        end_time=20.0,
        overall_score=80,
        audio_energy_score=80,
        scene_change_score=80,
        speech_density_score=80,
        keyword_score=80,
        rank=1,
        highlight_type=HighlightType.KEY_MOMENT,
    )
    db_session.add(highlight)

    with pytest.raises(IntegrityError):
        await db_session.commit()


@pytest.mark.asyncio
async def test_highlight_model_component_scores(db_session: AsyncSession):
    """Test Highlight model component scores (audio, scene, speech, keyword)."""
    # Create user and video
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

    # Create highlight with different component scores
    highlight = Highlight(
        video_id=video.id,
        start_time=5.0,
        end_time=15.0,
        overall_score=75,
        audio_energy_score=95,  # High audio energy
        scene_change_score=60,  # Moderate scene changes
        speech_density_score=70,  # Good speech density
        keyword_score=50,  # Some keywords
        rank=2,
        highlight_type=HighlightType.HIGH_ENERGY,
    )
    db_session.add(highlight)
    await db_session.commit()
    await db_session.refresh(highlight)

    assert highlight.audio_energy_score == 95
    assert highlight.scene_change_score == 60
    assert highlight.speech_density_score == 70
    assert highlight.keyword_score == 50
    # Verify scores are in valid range (0-100)
    assert 0 <= highlight.audio_energy_score <= 100
    assert 0 <= highlight.scene_change_score <= 100
    assert 0 <= highlight.speech_density_score <= 100
    assert 0 <= highlight.keyword_score <= 100


@pytest.mark.asyncio
async def test_highlight_model_detected_keywords_array(db_session: AsyncSession):
    """Test Highlight model detected_keywords array field storage and retrieval."""
    # Create user and video
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

    # Create highlight with detected keywords
    keywords = ["amazing", "incredible", "best"]
    highlight = Highlight(
        video_id=video.id,
        start_time=30.0,
        end_time=45.0,
        overall_score=90,
        audio_energy_score=85,
        scene_change_score=80,
        speech_density_score=88,
        keyword_score=95,  # High keyword score
        detected_keywords=keywords,
        rank=1,
        highlight_type=HighlightType.KEYWORD_MATCH,
    )
    db_session.add(highlight)
    await db_session.commit()
    await db_session.refresh(highlight)

    assert highlight.detected_keywords == keywords
    assert len(highlight.detected_keywords) == 3
    assert "amazing" in highlight.detected_keywords


@pytest.mark.asyncio
async def test_highlight_model_highlight_type_enum_validation(
    db_session: AsyncSession,
):
    """Test Highlight model highlight_type enum validation."""
    # Create user and video
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

    # Test all valid highlight types
    highlight_types = [
        HighlightType.HIGH_ENERGY,
        HighlightType.KEY_MOMENT,
        HighlightType.KEYWORD_MATCH,
        HighlightType.SCENE_CHANGE,
    ]

    for idx, hl_type in enumerate(highlight_types):
        highlight = Highlight(
            video_id=video.id,
            start_time=float(idx * 10),
            end_time=float((idx + 1) * 10),
            overall_score=75,
            audio_energy_score=75,
            scene_change_score=75,
            speech_density_score=75,
            keyword_score=75,
            rank=idx + 1,
            highlight_type=hl_type,
        )
        db_session.add(highlight)

    await db_session.commit()

    # Verify all highlights were created with correct types
    from sqlmodel import select

    result = await db_session.execute(
        select(Highlight).where(Highlight.video_id == video.id)
    )
    highlights = result.scalars().all()
    assert len(highlights) == 4


@pytest.mark.asyncio
async def test_highlight_model_status_enum_validation(db_session: AsyncSession):
    """Test Highlight model status enum validation."""
    # Create user and video
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

    # Test all valid status values
    statuses = [
        HighlightStatus.DETECTED,
        HighlightStatus.REVIEWED,
        HighlightStatus.EXPORTED,
        HighlightStatus.REJECTED,
    ]

    for idx, status in enumerate(statuses):
        highlight = Highlight(
            video_id=video.id,
            start_time=float(idx * 10),
            end_time=float((idx + 1) * 10),
            overall_score=75,
            audio_energy_score=75,
            scene_change_score=75,
            speech_density_score=75,
            keyword_score=75,
            rank=idx + 1,
            highlight_type=HighlightType.KEY_MOMENT,
            status=status,
        )
        db_session.add(highlight)

    await db_session.commit()

    # Verify all highlights were created with correct statuses
    from sqlmodel import select

    result = await db_session.execute(
        select(Highlight).where(Highlight.video_id == video.id)
    )
    highlights = result.scalars().all()
    assert len(highlights) == 4


@pytest.mark.asyncio
async def test_highlight_model_relationship_with_video(db_session: AsyncSession):
    """Test Highlight model relationship with Video."""
    # Create user and video
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

    # Create multiple highlights for the video
    for i in range(3):
        highlight = Highlight(
            video_id=video.id,
            start_time=float(i * 10),
            end_time=float((i + 1) * 10),
            overall_score=75 + i,
            audio_energy_score=75,
            scene_change_score=75,
            speech_density_score=75,
            keyword_score=75,
            rank=i + 1,
            highlight_type=HighlightType.KEY_MOMENT,
        )
        db_session.add(highlight)

    await db_session.commit()

    # Query highlights for video
    from sqlmodel import select

    result = await db_session.execute(
        select(Highlight).where(Highlight.video_id == video.id)
    )
    highlights = result.scalars().all()

    assert len(highlights) == 3
    assert all(h.video_id == video.id for h in highlights)


@pytest.mark.asyncio
async def test_highlight_model_timestamps(db_session: AsyncSession):
    """Test Highlight model timestamps (created_at, updated_at)."""
    # Create user and video
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

    # Create highlight
    highlight = Highlight(
        video_id=video.id,
        start_time=10.0,
        end_time=20.0,
        overall_score=80,
        audio_energy_score=80,
        scene_change_score=80,
        speech_density_score=80,
        keyword_score=80,
        rank=1,
        highlight_type=HighlightType.KEY_MOMENT,
    )
    db_session.add(highlight)
    await db_session.commit()
    await db_session.refresh(highlight)

    assert highlight.created_at is not None
    assert highlight.updated_at is not None
    assert highlight.created_at <= highlight.updated_at
