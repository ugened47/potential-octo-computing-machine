"""Tests for VideoExport model."""

from datetime import datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    CropStrategy,
    ExportStatus,
    PlatformType,
    SocialMediaTemplate,
    StylePreset,
    User,
    Video,
    VideoExport,
    VideoStatus,
)


@pytest.mark.asyncio
async def test_export_creation_with_required_fields(db_session: AsyncSession):
    """Test VideoExport model creation with required fields."""
    # Create user
    user = User(email="test@example.com", hashed_password="hashed")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Create video
    video = Video(
        user_id=user.id,
        title="Test Video",
        status=VideoStatus.COMPLETED,
    )
    db_session.add(video)
    await db_session.commit()
    await db_session.refresh(video)

    # Create template
    template = SocialMediaTemplate(
        name="YouTube Shorts",
        platform=PlatformType.YOUTUBE_SHORTS,
        aspect_ratio="9:16",
        max_duration_seconds=60,
        style_preset=StylePreset.BOLD,
    )
    db_session.add(template)
    await db_session.commit()
    await db_session.refresh(template)

    # Create export
    export = VideoExport(
        video_id=video.id,
        template_id=template.id,
        status=ExportStatus.PROCESSING,
        crop_strategy=CropStrategy.BLUR,
    )
    db_session.add(export)
    await db_session.commit()
    await db_session.refresh(export)

    assert export.id is not None
    assert export.video_id == video.id
    assert export.template_id == template.id
    assert export.status == ExportStatus.PROCESSING
    assert export.crop_strategy == CropStrategy.BLUR
    assert export.created_at is not None
    assert export.updated_at is not None


@pytest.mark.asyncio
async def test_export_model_status_transitions(db_session: AsyncSession):
    """Test VideoExport model status transitions (processing → completed/failed)."""
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
        name="TikTok",
        platform=PlatformType.TIKTOK,
        aspect_ratio="9:16",
        max_duration_seconds=60,
        style_preset=StylePreset.TRENDY,
    )
    db_session.add(template)
    await db_session.commit()
    await db_session.refresh(template)

    # Test processing → completed transition
    export1 = VideoExport(
        video_id=video.id,
        template_id=template.id,
        status=ExportStatus.PROCESSING,
        crop_strategy=CropStrategy.SMART,
    )
    db_session.add(export1)
    await db_session.commit()
    await db_session.refresh(export1)

    export1.status = ExportStatus.COMPLETED
    export1.export_url = "https://s3.amazonaws.com/bucket/export1.mp4"
    export1.file_size = 1024 * 1024 * 50  # 50 MB
    export1.completed_at = datetime.utcnow()
    await db_session.commit()
    await db_session.refresh(export1)

    assert export1.status == ExportStatus.COMPLETED
    assert export1.export_url is not None
    assert export1.completed_at is not None

    # Test processing → failed transition
    export2 = VideoExport(
        video_id=video.id,
        template_id=template.id,
        status=ExportStatus.PROCESSING,
        crop_strategy=CropStrategy.CENTER,
    )
    db_session.add(export2)
    await db_session.commit()
    await db_session.refresh(export2)

    export2.status = ExportStatus.FAILED
    export2.error_message = "FFmpeg encoding error"
    await db_session.commit()
    await db_session.refresh(export2)

    assert export2.status == ExportStatus.FAILED
    assert export2.error_message == "FFmpeg encoding error"


@pytest.mark.asyncio
async def test_export_model_segment_times(db_session: AsyncSession):
    """Test VideoExport model segment times (start/end) validation."""
    # Create dependencies
    user = User(email="test@example.com", hashed_password="hashed")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    video = Video(
        user_id=user.id,
        title="Test Video",
        status=VideoStatus.COMPLETED,
        duration=120.0,
    )
    db_session.add(video)
    await db_session.commit()
    await db_session.refresh(video)

    template = SocialMediaTemplate(
        name="Instagram Reels",
        platform=PlatformType.INSTAGRAM_REELS,
        aspect_ratio="9:16",
        max_duration_seconds=90,
        style_preset=StylePreset.VLOG,
    )
    db_session.add(template)
    await db_session.commit()
    await db_session.refresh(template)

    # Test with segment times
    export = VideoExport(
        video_id=video.id,
        template_id=template.id,
        status=ExportStatus.PROCESSING,
        crop_strategy=CropStrategy.LETTERBOX,
        segment_start_time=10.5,
        segment_end_time=70.5,
    )
    db_session.add(export)
    await db_session.commit()
    await db_session.refresh(export)

    assert export.segment_start_time == 10.5
    assert export.segment_end_time == 70.5
    assert export.segment_end_time > export.segment_start_time


@pytest.mark.asyncio
async def test_export_model_crop_strategy_enum(db_session: AsyncSession):
    """Test VideoExport model crop_strategy enum values."""
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
        name="LinkedIn",
        platform=PlatformType.LINKEDIN,
        aspect_ratio="1:1",
        max_duration_seconds=600,
        style_preset=StylePreset.PROFESSIONAL,
    )
    db_session.add(template)
    await db_session.commit()
    await db_session.refresh(template)

    # Test all crop strategy enum values
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
            status=ExportStatus.PROCESSING,
            crop_strategy=strategy,
        )
        db_session.add(export)
        await db_session.commit()
        await db_session.refresh(export)

        assert export.crop_strategy == strategy


@pytest.mark.asyncio
async def test_export_model_metadata_fields(db_session: AsyncSession):
    """Test VideoExport model metadata fields (file_size, resolution, duration)."""
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
        name="Twitter",
        platform=PlatformType.TWITTER,
        aspect_ratio="16:9",
        max_duration_seconds=140,
        style_preset=StylePreset.MINIMAL,
    )
    db_session.add(template)
    await db_session.commit()
    await db_session.refresh(template)

    # Create export with metadata
    export = VideoExport(
        video_id=video.id,
        template_id=template.id,
        status=ExportStatus.COMPLETED,
        crop_strategy=CropStrategy.CENTER,
        export_url="https://s3.amazonaws.com/bucket/export.mp4",
        file_size=1024 * 1024 * 75,  # 75 MB
        resolution="1080x1920",
        duration_seconds=60.0,
    )
    db_session.add(export)
    await db_session.commit()
    await db_session.refresh(export)

    assert export.file_size == 1024 * 1024 * 75
    assert export.resolution == "1080x1920"
    assert export.duration_seconds == 60.0
    assert export.export_url is not None


@pytest.mark.asyncio
async def test_export_model_relationships(db_session: AsyncSession):
    """Test VideoExport model relationships with Video and Template."""
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
        name="Custom Template",
        platform=PlatformType.CUSTOM,
        aspect_ratio="4:3",
        max_duration_seconds=300,
        style_preset=StylePreset.CUSTOM,
    )
    db_session.add(template)
    await db_session.commit()
    await db_session.refresh(template)

    # Create export
    export = VideoExport(
        video_id=video.id,
        template_id=template.id,
        status=ExportStatus.PROCESSING,
        crop_strategy=CropStrategy.SMART,
    )
    db_session.add(export)
    await db_session.commit()
    await db_session.refresh(export)

    # Verify relationships
    assert export.video_id == video.id
    assert export.template_id == template.id


@pytest.mark.asyncio
async def test_export_model_timestamps(db_session: AsyncSession):
    """Test VideoExport model timestamps are automatically set."""
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
        style_preset=StylePreset.BOLD,
    )
    db_session.add(template)
    await db_session.commit()
    await db_session.refresh(template)

    # Create export
    export = VideoExport(
        video_id=video.id,
        template_id=template.id,
        status=ExportStatus.PROCESSING,
        crop_strategy=CropStrategy.BLUR,
    )
    db_session.add(export)
    await db_session.commit()
    await db_session.refresh(export)

    assert export.created_at is not None
    assert export.updated_at is not None
    # Timestamps should be set and very close (within 1 second)
    assert abs((export.created_at - export.updated_at).total_seconds()) < 1
    # Both should be recent (within last minute)
    now = datetime.utcnow()
    assert abs((now - export.created_at).total_seconds()) < 60
    assert abs((now - export.updated_at).total_seconds()) < 60


@pytest.mark.asyncio
async def test_export_model_optional_fields(db_session: AsyncSession):
    """Test VideoExport model optional fields can be None."""
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
        platform=PlatformType.TIKTOK,
        aspect_ratio="9:16",
        max_duration_seconds=60,
        style_preset=StylePreset.TRENDY,
    )
    db_session.add(template)
    await db_session.commit()
    await db_session.refresh(template)

    # Create export with minimal fields
    export = VideoExport(
        video_id=video.id,
        template_id=template.id,
        status=ExportStatus.PROCESSING,
        crop_strategy=CropStrategy.SMART,
        export_url=None,
        file_size=None,
        resolution=None,
        duration_seconds=None,
        segment_start_time=None,
        segment_end_time=None,
        error_message=None,
        completed_at=None,
    )
    db_session.add(export)
    await db_session.commit()
    await db_session.refresh(export)

    assert export.export_url is None
    assert export.file_size is None
    assert export.resolution is None
    assert export.duration_seconds is None
    assert export.segment_start_time is None
    assert export.segment_end_time is None
    assert export.error_message is None
    assert export.completed_at is None
