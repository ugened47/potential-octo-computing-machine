"""Tests for SocialMediaTemplate model."""

from datetime import datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import PlatformType, SocialMediaTemplate, StylePreset, User


@pytest.mark.asyncio
async def test_template_creation_with_required_fields(db_session: AsyncSession):
    """Test SocialMediaTemplate model creation with required fields."""
    template = SocialMediaTemplate(
        name="YouTube Shorts Test",
        platform=PlatformType.YOUTUBE_SHORTS,
        aspect_ratio="9:16",
        max_duration_seconds=60,
        style_preset=StylePreset.BOLD,
    )
    db_session.add(template)
    await db_session.commit()
    await db_session.refresh(template)

    assert template.id is not None
    assert template.name == "YouTube Shorts Test"
    assert template.platform == PlatformType.YOUTUBE_SHORTS
    assert template.aspect_ratio == "9:16"
    assert template.max_duration_seconds == 60
    assert template.style_preset == StylePreset.BOLD
    assert template.created_at is not None
    assert template.updated_at is not None


@pytest.mark.asyncio
async def test_template_model_validation_platform_enum(db_session: AsyncSession):
    """Test SocialMediaTemplate model validation for platform enum."""
    platforms = [
        PlatformType.YOUTUBE_SHORTS,
        PlatformType.TIKTOK,
        PlatformType.INSTAGRAM_REELS,
        PlatformType.TWITTER,
        PlatformType.LINKEDIN,
        PlatformType.CUSTOM,
    ]

    for platform in platforms:
        template = SocialMediaTemplate(
            name=f"{platform.value} Template",
            platform=platform,
            aspect_ratio="9:16",
            max_duration_seconds=60,
            style_preset=StylePreset.MINIMAL,
        )
        db_session.add(template)
        await db_session.commit()
        await db_session.refresh(template)

        assert template.platform == platform


@pytest.mark.asyncio
async def test_template_caption_style_jsonb_field(db_session: AsyncSession):
    """Test SocialMediaTemplate caption_style JSONB field storage and retrieval."""
    caption_style = {
        "font_family": "Arial Bold",
        "font_size": 6,
        "font_weight": "extra-bold",
        "text_color": "#FFFFFF",
        "background_color": "#000000CC",
        "stroke_color": "#000000",
        "stroke_width": 2,
        "position": "bottom",
        "y_offset": 85,
        "alignment": "center",
        "animation": "pop",
        "max_chars_per_line": 30,
        "max_lines": 2,
    }

    template = SocialMediaTemplate(
        name="TikTok Template",
        platform=PlatformType.TIKTOK,
        aspect_ratio="9:16",
        max_duration_seconds=60,
        style_preset=StylePreset.TRENDY,
        caption_style=caption_style,
    )
    db_session.add(template)
    await db_session.commit()
    await db_session.refresh(template)

    assert template.caption_style is not None
    assert template.caption_style["font_family"] == "Arial Bold"
    assert template.caption_style["font_size"] == 6
    assert template.caption_style["text_color"] == "#FFFFFF"
    assert template.caption_style["max_lines"] == 2


@pytest.mark.asyncio
async def test_template_system_preset_vs_user_template(db_session: AsyncSession):
    """Test SocialMediaTemplate differentiation between system presets and user templates."""
    # Create user first
    user = User(email="test@example.com", hashed_password="hashed")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Create system preset (no user_id)
    system_template = SocialMediaTemplate(
        name="System YouTube Shorts",
        platform=PlatformType.YOUTUBE_SHORTS,
        aspect_ratio="9:16",
        max_duration_seconds=60,
        style_preset=StylePreset.BOLD,
        is_system_preset=True,
        user_id=None,
    )
    db_session.add(system_template)

    # Create user template
    user_template = SocialMediaTemplate(
        name="My Custom Template",
        platform=PlatformType.TIKTOK,
        aspect_ratio="9:16",
        max_duration_seconds=30,
        style_preset=StylePreset.CUSTOM,
        is_system_preset=False,
        user_id=user.id,
    )
    db_session.add(user_template)

    await db_session.commit()
    await db_session.refresh(system_template)
    await db_session.refresh(user_template)

    assert system_template.is_system_preset is True
    assert system_template.user_id is None

    assert user_template.is_system_preset is False
    assert user_template.user_id == user.id


@pytest.mark.asyncio
async def test_template_relationships_with_user(db_session: AsyncSession):
    """Test SocialMediaTemplate relationships with User."""
    user = User(email="test@example.com", hashed_password="hashed")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    template = SocialMediaTemplate(
        name="User's Template",
        platform=PlatformType.INSTAGRAM_REELS,
        aspect_ratio="9:16",
        max_duration_seconds=90,
        style_preset=StylePreset.VLOG,
        user_id=user.id,
    )
    db_session.add(template)
    await db_session.commit()
    await db_session.refresh(template)

    assert template.user_id == user.id


@pytest.mark.asyncio
async def test_template_timestamps_auto_set(db_session: AsyncSession):
    """Test SocialMediaTemplate timestamps are automatically set."""
    template = SocialMediaTemplate(
        name="LinkedIn Template",
        platform=PlatformType.LINKEDIN,
        aspect_ratio="1:1",
        max_duration_seconds=600,
        style_preset=StylePreset.PROFESSIONAL,
    )
    db_session.add(template)
    await db_session.commit()
    await db_session.refresh(template)

    assert template.created_at is not None
    assert template.updated_at is not None
    # Timestamps should be set and very close (within 1 second)
    assert abs((template.created_at - template.updated_at).total_seconds()) < 1
    # Both should be recent (within last minute)
    now = datetime.utcnow()
    assert abs((now - template.created_at).total_seconds()) < 60
    assert abs((now - template.updated_at).total_seconds()) < 60


@pytest.mark.asyncio
async def test_template_default_values(db_session: AsyncSession):
    """Test SocialMediaTemplate default values for optional fields."""
    template = SocialMediaTemplate(
        name="Default Template",
        platform=PlatformType.TWITTER,
        aspect_ratio="16:9",
        max_duration_seconds=140,
        style_preset=StylePreset.MINIMAL,
    )
    db_session.add(template)
    await db_session.commit()
    await db_session.refresh(template)

    # Check default values
    assert template.auto_captions is True
    assert template.video_codec == "h264"
    assert template.audio_codec == "aac"
    assert template.bitrate == "5M"
    assert template.is_system_preset is False
    assert template.is_active is True
    assert template.usage_count == 0


@pytest.mark.asyncio
async def test_template_style_preset_enum(db_session: AsyncSession):
    """Test SocialMediaTemplate style_preset enum values."""
    style_presets = [
        StylePreset.MINIMAL,
        StylePreset.BOLD,
        StylePreset.GAMING,
        StylePreset.PODCAST,
        StylePreset.VLOG,
        StylePreset.PROFESSIONAL,
        StylePreset.TRENDY,
        StylePreset.CUSTOM,
    ]

    for preset in style_presets:
        template = SocialMediaTemplate(
            name=f"{preset.value} Template",
            platform=PlatformType.YOUTUBE_SHORTS,
            aspect_ratio="9:16",
            max_duration_seconds=60,
            style_preset=preset,
        )
        db_session.add(template)
        await db_session.commit()
        await db_session.refresh(template)

        assert template.style_preset == preset
