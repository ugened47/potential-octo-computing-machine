"""Tests for VideoExport model."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    CropStrategy,
    ExportStatus,
    PlatformType,
    SocialMediaTemplate,
    VideoExport,
)
from app.models.user import User
from app.models.video import Video, VideoStatus


@pytest.mark.asyncio
async def test_export_creation_with_required_fields(db_session: AsyncSession):
    """Test VideoExport model creation with required fields."""
    # Create user, video, and template
    user = User(email="test@example.com", hashed_password="hashed")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    video = Video(
        user_id=user.id,
        title="Test Video",
        status=VideoStatus.COMPLETED,
    )
    db_session.add(video)
    await db_session.commit()
    await db_session.refresh(video)

    template = SocialMediaTemplate(
        name="Test Template",
        platform=PlatformType.YOUTUBE_SHORTS,
        aspect_ratio="9:16",
        max_duration_seconds=60,
    )
    db_session.add(template)
    await db_session.commit()
    await db_session.refresh(template)

    # Create export
    export = VideoExport(
        video_id=video.id,
        template_id=template.id,
        crop_strategy=CropStrategy.SMART,
        status=ExportStatus.PROCESSING,
    )
    db_session.add(export)
    await db_session.commit()
    await db_session.refresh(export)

    assert export.id is not None
    assert export.video_id == video.id
    assert export.template_id == template.id
    assert export.crop_strategy == CropStrategy.SMART
    assert export.status == ExportStatus.PROCESSING
    assert export.created_at is not None
    assert export.updated_at is not None


@pytest.mark.asyncio
async def test_export_status_transitions(db_session: AsyncSession):
    """Test VideoExport model status transitions."""
    # Create dependencies
    user = User(email="test@example.com", hashed_password="hashed")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    video = Video(user_id=user.id, title="Test Video", status=VideoStatus.COMPLETED)
    db_session.add(video)
    await db_session.commit()
    await db_session.refresh(video)

    template = SocialMediaTemplate(
        name="Test Template",
        platform=PlatformType.YOUTUBE_SHORTS,
        aspect_ratio="9:16",
        max_duration_seconds=60,
    )
    db_session.add(template)
    await db_session.commit()
    await db_session.refresh(template)

    # Test status transitions
    statuses = [ExportStatus.PROCESSING, ExportStatus.COMPLETED, ExportStatus.FAILED]

    for status in statuses:
        export = VideoExport(
            video_id=video.id,
            template_id=template.id,
            status=status,
        )
        db_session.add(export)
        await db_session.commit()
        await db_session.refresh(export)

        assert export.status == status


@pytest.mark.asyncio
async def test_export_crop_strategy_enum(db_session: AsyncSession):
    """Test VideoExport crop_strategy enum values."""
    # Create dependencies
    user = User(email="test@example.com", hashed_password="hashed")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    video = Video(user_id=user.id, title="Test Video", status=VideoStatus.COMPLETED)
    db_session.add(video)
    await db_session.commit()
    await db_session.refresh(video)

    template = SocialMediaTemplate(
        name="Test Template",
        platform=PlatformType.YOUTUBE_SHORTS,
        aspect_ratio="9:16",
        max_duration_seconds=60,
    )
    db_session.add(template)
    await db_session.commit()
    await db_session.refresh(template)

    # Test all crop strategies
    strategies = [
        CropStrategy.SMART,
        CropStrategy.CENTER,
        CropStrategy.LETTERBOX,
        CropStrategy.BLUR,
    ]

    for strategy in strategies:
        export = VideoExport(
            video_id=video.id,
            template_id=template.id,
            crop_strategy=strategy,
        )
        db_session.add(export)
        await db_session.commit()
        await db_session.refresh(export)

        assert export.crop_strategy == strategy


@pytest.mark.asyncio
async def test_export_file_metadata(db_session: AsyncSession):
    """Test VideoExport file metadata fields."""
    # Create dependencies
    user = User(email="test@example.com", hashed_password="hashed")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    video = Video(user_id=user.id, title="Test Video", status=VideoStatus.COMPLETED)
    db_session.add(video)
    await db_session.commit()
    await db_session.refresh(video)

    template = SocialMediaTemplate(
        name="Test Template",
        platform=PlatformType.YOUTUBE_SHORTS,
        aspect_ratio="9:16",
        max_duration_seconds=60,
    )
    db_session.add(template)
    await db_session.commit()
    await db_session.refresh(template)

    # Create export with file metadata
    export = VideoExport(
        video_id=video.id,
        template_id=template.id,
        status=ExportStatus.COMPLETED,
        export_url="https://cdn.example.com/exports/test.mp4",
        s3_key="exports/test-uuid.mp4",
        file_size=1024 * 1024 * 50,  # 50 MB
        resolution="1080x1920",
        duration_seconds=58.5,
    )
    db_session.add(export)
    await db_session.commit()
    await db_session.refresh(export)

    assert export.export_url == "https://cdn.example.com/exports/test.mp4"
    assert export.s3_key == "exports/test-uuid.mp4"
    assert export.file_size == 1024 * 1024 * 50
    assert export.resolution == "1080x1920"
    assert export.duration_seconds == 58.5


@pytest.mark.asyncio
async def test_export_segment_times(db_session: AsyncSession):
    """Test VideoExport segment time fields."""
    # Create dependencies
    user = User(email="test@example.com", hashed_password="hashed")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    video = Video(user_id=user.id, title="Test Video", status=VideoStatus.COMPLETED)
    db_session.add(video)
    await db_session.commit()
    await db_session.refresh(video)

    template = SocialMediaTemplate(
        name="Test Template",
        platform=PlatformType.YOUTUBE_SHORTS,
        aspect_ratio="9:16",
        max_duration_seconds=60,
    )
    db_session.add(template)
    await db_session.commit()
    await db_session.refresh(template)

    # Create export with segment times
    export = VideoExport(
        video_id=video.id,
        template_id=template.id,
        segment_start_time=10.5,
        segment_end_time=70.5,
    )
    db_session.add(export)
    await db_session.commit()
    await db_session.refresh(export)

    assert export.segment_start_time == 10.5
    assert export.segment_end_time == 70.5


@pytest.mark.asyncio
async def test_export_error_message(db_session: AsyncSession):
    """Test VideoExport error_message field for failed exports."""
    # Create dependencies
    user = User(email="test@example.com", hashed_password="hashed")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    video = Video(user_id=user.id, title="Test Video", status=VideoStatus.COMPLETED)
    db_session.add(video)
    await db_session.commit()
    await db_session.refresh(video)

    template = SocialMediaTemplate(
        name="Test Template",
        platform=PlatformType.YOUTUBE_SHORTS,
        aspect_ratio="9:16",
        max_duration_seconds=60,
    )
    db_session.add(template)
    await db_session.commit()
    await db_session.refresh(template)

    # Create failed export with error message
    export = VideoExport(
        video_id=video.id,
        template_id=template.id,
        status=ExportStatus.FAILED,
        error_message="FFmpeg encoding failed: invalid codec parameters",
    )
    db_session.add(export)
    await db_session.commit()
    await db_session.refresh(export)

    assert export.status == ExportStatus.FAILED
    assert export.error_message == "FFmpeg encoding failed: invalid codec parameters"


@pytest.mark.asyncio
async def test_export_default_values(db_session: AsyncSession):
    """Test VideoExport default values."""
    # Create dependencies
    user = User(email="test@example.com", hashed_password="hashed")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    video = Video(user_id=user.id, title="Test Video", status=VideoStatus.COMPLETED)
    db_session.add(video)
    await db_session.commit()
    await db_session.refresh(video)

    template = SocialMediaTemplate(
        name="Test Template",
        platform=PlatformType.YOUTUBE_SHORTS,
        aspect_ratio="9:16",
        max_duration_seconds=60,
    )
    db_session.add(template)
    await db_session.commit()
    await db_session.refresh(template)

    # Create export with minimal fields
    export = VideoExport(
        video_id=video.id,
        template_id=template.id,
    )
    db_session.add(export)
    await db_session.commit()
    await db_session.refresh(export)

    assert export.status == ExportStatus.PROCESSING
    assert export.crop_strategy == CropStrategy.SMART
    assert export.export_url is None
    assert export.s3_key is None
    assert export.file_size is None
    assert export.resolution is None
    assert export.duration_seconds is None
    assert export.segment_start_time is None
    assert export.segment_end_time is None
    assert export.error_message is None
    assert export.completed_at is None


@pytest.mark.asyncio
async def test_export_relationships(db_session: AsyncSession):
    """Test VideoExport relationships with Video and SocialMediaTemplate."""
    # Create dependencies
    user = User(email="test@example.com", hashed_password="hashed")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    video = Video(user_id=user.id, title="Test Video", status=VideoStatus.COMPLETED)
    db_session.add(video)
    await db_session.commit()
    await db_session.refresh(video)

    template = SocialMediaTemplate(
        name="Test Template",
        platform=PlatformType.YOUTUBE_SHORTS,
        aspect_ratio="9:16",
        max_duration_seconds=60,
    )
    db_session.add(template)
    await db_session.commit()
    await db_session.refresh(template)

    # Create export
    export = VideoExport(
        video_id=video.id,
        template_id=template.id,
    )
    db_session.add(export)
    await db_session.commit()
    await db_session.refresh(export)

    # Verify relationships
    assert export.video_id == video.id
    assert export.template_id == template.id
