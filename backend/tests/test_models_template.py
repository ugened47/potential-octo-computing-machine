"""Tests for SocialMediaTemplate model."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import PlatformType, SocialMediaTemplate, StylePreset
from app.models.user import User


@pytest.mark.asyncio
async def test_template_creation_with_required_fields(db_session: AsyncSession):
    """Test SocialMediaTemplate model creation with required fields."""
    template = SocialMediaTemplate(
        name="Test Template",
        platform=PlatformType.YOUTUBE_SHORTS,
        aspect_ratio="9:16",
        max_duration_seconds=60,
        auto_captions=True,
        caption_style={"font_family": "Arial", "font_size": 4},
        style_preset=StylePreset.BOLD,
        is_system_preset=False,
    )
    db_session.add(template)
    await db_session.commit()
    await db_session.refresh(template)

    assert template.id is not None
    assert template.name == "Test Template"
    assert template.platform == PlatformType.YOUTUBE_SHORTS
    assert template.aspect_ratio == "9:16"
    assert template.max_duration_seconds == 60
    assert template.auto_captions is True
    assert template.caption_style == {"font_family": "Arial", "font_size": 4}
    assert template.style_preset == StylePreset.BOLD
    assert template.created_at is not None
    assert template.updated_at is not None


@pytest.mark.asyncio
async def test_template_platform_enum_validation(db_session: AsyncSession):
    """Test SocialMediaTemplate model platform enum validation."""
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
            name=f"Test {platform.value}",
            platform=platform,
            aspect_ratio="9:16",
            max_duration_seconds=60,
        )
        db_session.add(template)
        await db_session.commit()
        await db_session.refresh(template)

        assert template.platform == platform


@pytest.mark.asyncio
async def test_template_style_preset_enum_validation(db_session: AsyncSession):
    """Test SocialMediaTemplate style preset enum validation."""
    presets = [
        StylePreset.MINIMAL,
        StylePreset.BOLD,
        StylePreset.GAMING,
        StylePreset.PODCAST,
        StylePreset.VLOG,
        StylePreset.PROFESSIONAL,
        StylePreset.TRENDY,
        StylePreset.CUSTOM,
    ]

    for preset in presets:
        template = SocialMediaTemplate(
            name=f"Test {preset.value}",
            platform=PlatformType.YOUTUBE_SHORTS,
            aspect_ratio="9:16",
            max_duration_seconds=60,
            style_preset=preset,
        )
        db_session.add(template)
        await db_session.commit()
        await db_session.refresh(template)

        assert template.style_preset == preset


@pytest.mark.asyncio
async def test_template_caption_style_jsonb_storage(db_session: AsyncSession):
    """Test SocialMediaTemplate caption_style JSONB field storage and retrieval."""
    caption_style = {
        "font_family": "Arial Black",
        "font_size": 6,
        "font_weight": "bold",
        "text_color": "#FFFFFF",
        "background_color": "rgba(255, 215, 0, 0.9)",
        "stroke_color": "#000000",
        "stroke_width": 3,
        "position": "bottom",
        "y_offset": 15,
        "alignment": "center",
        "animation": "pop",
        "max_chars_per_line": 30,
        "max_lines": 2,
    }

    template = SocialMediaTemplate(
        name="Test Caption Style",
        platform=PlatformType.YOUTUBE_SHORTS,
        aspect_ratio="9:16",
        max_duration_seconds=60,
        caption_style=caption_style,
    )
    db_session.add(template)
    await db_session.commit()
    await db_session.refresh(template)

    assert template.caption_style == caption_style
    assert template.caption_style["font_family"] == "Arial Black"
    assert template.caption_style["font_size"] == 6
    assert template.caption_style["animation"] == "pop"


@pytest.mark.asyncio
async def test_template_system_preset_vs_user_template(db_session: AsyncSession):
    """Test SocialMediaTemplate system preset vs user template differentiation."""
    # Create user
    user = User(email="test@example.com", hashed_password="hashed")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # System preset template
    system_template = SocialMediaTemplate(
        name="System Preset",
        platform=PlatformType.YOUTUBE_SHORTS,
        aspect_ratio="9:16",
        max_duration_seconds=60,
        is_system_preset=True,
        user_id=None,
    )
    db_session.add(system_template)

    # User custom template
    user_template = SocialMediaTemplate(
        name="User Template",
        platform=PlatformType.YOUTUBE_SHORTS,
        aspect_ratio="9:16",
        max_duration_seconds=60,
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
async def test_template_default_values(db_session: AsyncSession):
    """Test SocialMediaTemplate default values."""
    template = SocialMediaTemplate(
        name="Test Defaults",
        platform=PlatformType.YOUTUBE_SHORTS,
        aspect_ratio="9:16",
        max_duration_seconds=60,
    )
    db_session.add(template)
    await db_session.commit()
    await db_session.refresh(template)

    assert template.auto_captions is True
    assert template.caption_style == {}
    assert template.style_preset == StylePreset.MINIMAL
    assert template.video_codec == "h264"
    assert template.audio_codec == "aac"
    assert template.bitrate == "5M"
    assert template.is_system_preset is False
    assert template.user_id is None
    assert template.is_active is True
    assert template.usage_count == 0


@pytest.mark.asyncio
async def test_template_aspect_ratio_formats(db_session: AsyncSession):
    """Test various aspect ratio formats."""
    aspect_ratios = ["9:16", "16:9", "1:1", "4:5", "4:3", "21:9"]

    for aspect_ratio in aspect_ratios:
        template = SocialMediaTemplate(
            name=f"Test {aspect_ratio}",
            platform=PlatformType.CUSTOM,
            aspect_ratio=aspect_ratio,
            max_duration_seconds=60,
        )
        db_session.add(template)
        await db_session.commit()
        await db_session.refresh(template)

        assert template.aspect_ratio == aspect_ratio


@pytest.mark.asyncio
async def test_template_timestamps(db_session: AsyncSession):
    """Test SocialMediaTemplate timestamps are automatically set."""
    from datetime import datetime

    template = SocialMediaTemplate(
        name="Test Timestamps",
        platform=PlatformType.YOUTUBE_SHORTS,
        aspect_ratio="9:16",
        max_duration_seconds=60,
    )
    db_session.add(template)
    await db_session.commit()
    await db_session.refresh(template)

    assert template.created_at is not None
    assert template.updated_at is not None
    assert abs((template.created_at - template.updated_at).total_seconds()) < 1

    now = datetime.utcnow()
    assert abs((now - template.created_at).total_seconds()) < 60
    assert abs((now - template.updated_at).total_seconds()) < 60
