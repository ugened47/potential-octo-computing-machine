"""Tests for Subtitle models (SubtitleStyle, SubtitleTranslation, SubtitleStylePreset)."""

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subtitle import (
    AnimationType,
    FontWeight,
    Platform,
    PositionHorizontal,
    PositionVertical,
    SubtitleStyle,
    SubtitleStylePreset,
    SubtitleTranslation,
    TranslationQuality,
    TranslationStatus,
)
from app.models.user import User
from app.models.video import Video, VideoStatus


@pytest.mark.asyncio
async def test_subtitle_style_creation_with_defaults(db_session: AsyncSession):
    """Test SubtitleStyle model creation with default values."""
    # Create user and video first
    user = User(email="test@example.com", hashed_password="hashed")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    video = Video(user_id=user.id, title="Test Video", status=VideoStatus.UPLOADED)
    db_session.add(video)
    await db_session.commit()
    await db_session.refresh(video)

    # Create subtitle style with defaults
    style = SubtitleStyle(
        video_id=video.id,
        language_code="en",
        created_by=user.id,
    )
    db_session.add(style)
    await db_session.commit()
    await db_session.refresh(style)

    # Verify defaults
    assert style.id is not None
    assert style.video_id == video.id
    assert style.language_code == "en"
    assert style.font_family == "Arial"
    assert style.font_size == 24
    assert style.font_weight == FontWeight.BOLD
    assert style.font_color == "#FFFFFF"
    assert style.font_alpha == 1.0
    assert style.background_enabled is True
    assert style.background_color == "#000000"
    assert style.background_alpha == 0.7
    assert style.outline_enabled is True
    assert style.outline_color == "#000000"
    assert style.outline_width == 2
    assert style.position_vertical == PositionVertical.BOTTOM
    assert style.position_horizontal == PositionHorizontal.CENTER
    assert style.margin_vertical == 50
    assert style.margin_horizontal == 40
    assert style.max_width_percent == 80
    assert style.words_per_line == 7
    assert style.max_lines == 2
    assert style.animation_type == AnimationType.NONE
    assert style.created_at is not None
    assert style.updated_at is not None


@pytest.mark.asyncio
async def test_subtitle_style_unique_constraint(db_session: AsyncSession):
    """Test SubtitleStyle unique constraint on (video_id, language_code)."""
    user = User(email="test@example.com", hashed_password="hashed")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    video = Video(user_id=user.id, title="Test Video", status=VideoStatus.UPLOADED)
    db_session.add(video)
    await db_session.commit()
    await db_session.refresh(video)

    # Create first style
    style1 = SubtitleStyle(
        video_id=video.id,
        language_code="en",
        created_by=user.id,
    )
    db_session.add(style1)
    await db_session.commit()

    # Try to create duplicate (same video_id and language_code)
    style2 = SubtitleStyle(
        video_id=video.id,
        language_code="en",
        created_by=user.id,
    )
    db_session.add(style2)

    with pytest.raises(IntegrityError):
        await db_session.commit()


@pytest.mark.asyncio
async def test_subtitle_style_custom_properties(db_session: AsyncSession):
    """Test SubtitleStyle with custom property values."""
    user = User(email="test@example.com", hashed_password="hashed")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    video = Video(user_id=user.id, title="Test Video", status=VideoStatus.UPLOADED)
    db_session.add(video)
    await db_session.commit()
    await db_session.refresh(video)

    # Create with custom values
    style = SubtitleStyle(
        video_id=video.id,
        language_code="es",
        created_by=user.id,
        font_family="Roboto",
        font_size=36,
        font_weight=FontWeight.NORMAL,
        font_color="#FFD700",
        background_enabled=False,
        outline_width=4,
        position_vertical=PositionVertical.TOP,
        position_horizontal=PositionHorizontal.LEFT,
        animation_type=AnimationType.FADE,
        preset_name="Custom Preset",
    )
    db_session.add(style)
    await db_session.commit()
    await db_session.refresh(style)

    assert style.font_family == "Roboto"
    assert style.font_size == 36
    assert style.font_weight == FontWeight.NORMAL
    assert style.font_color == "#FFD700"
    assert style.background_enabled is False
    assert style.outline_width == 4
    assert style.position_vertical == PositionVertical.TOP
    assert style.position_horizontal == PositionHorizontal.LEFT
    assert style.animation_type == AnimationType.FADE
    assert style.preset_name == "Custom Preset"


@pytest.mark.asyncio
async def test_subtitle_translation_creation(db_session: AsyncSession):
    """Test SubtitleTranslation model creation with required fields."""
    user = User(email="test@example.com", hashed_password="hashed")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    video = Video(user_id=user.id, title="Test Video", status=VideoStatus.UPLOADED)
    db_session.add(video)
    await db_session.commit()
    await db_session.refresh(video)

    # Create translation
    translation = SubtitleTranslation(
        video_id=video.id,
        source_language="en",
        target_language="es",
        segments={"segments": []},
    )
    db_session.add(translation)
    await db_session.commit()
    await db_session.refresh(translation)

    assert translation.id is not None
    assert translation.video_id == video.id
    assert translation.source_language == "en"
    assert translation.target_language == "es"
    assert translation.translation_service == "google"
    assert translation.translation_quality == TranslationQuality.MACHINE
    assert translation.status == TranslationStatus.PENDING
    assert translation.character_count == 0
    assert translation.word_count == 0
    assert translation.created_at is not None


@pytest.mark.asyncio
async def test_subtitle_translation_unique_constraint(db_session: AsyncSession):
    """Test SubtitleTranslation unique constraint on (video_id, target_language)."""
    user = User(email="test@example.com", hashed_password="hashed")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    video = Video(user_id=user.id, title="Test Video", status=VideoStatus.UPLOADED)
    db_session.add(video)
    await db_session.commit()
    await db_session.refresh(video)

    # Create first translation
    translation1 = SubtitleTranslation(
        video_id=video.id,
        source_language="en",
        target_language="es",
        segments={"segments": []},
    )
    db_session.add(translation1)
    await db_session.commit()

    # Try to create duplicate (same video_id and target_language)
    translation2 = SubtitleTranslation(
        video_id=video.id,
        source_language="en",
        target_language="es",
        segments={"segments": []},
    )
    db_session.add(translation2)

    with pytest.raises(IntegrityError):
        await db_session.commit()


@pytest.mark.asyncio
async def test_subtitle_translation_with_segments(db_session: AsyncSession):
    """Test SubtitleTranslation with translation segments data."""
    user = User(email="test@example.com", hashed_password="hashed")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    video = Video(user_id=user.id, title="Test Video", status=VideoStatus.UPLOADED)
    db_session.add(video)
    await db_session.commit()
    await db_session.refresh(video)

    # Create translation with segments
    segments_data = {
        "segments": [
            {
                "start_time": 0.0,
                "end_time": 2.5,
                "original_text": "Hello world",
                "translated_text": "Hola mundo",
                "confidence": 0.95,
            },
            {
                "start_time": 2.5,
                "end_time": 5.0,
                "original_text": "Welcome",
                "translated_text": "Bienvenido",
                "confidence": 0.98,
            },
        ]
    }

    translation = SubtitleTranslation(
        video_id=video.id,
        source_language="en",
        target_language="es",
        segments=segments_data,
        character_count=30,
        word_count=5,
        status=TranslationStatus.COMPLETED,
        translation_quality=TranslationQuality.REVIEWED,
    )
    db_session.add(translation)
    await db_session.commit()
    await db_session.refresh(translation)

    assert translation.segments == segments_data
    assert translation.character_count == 30
    assert translation.word_count == 5
    assert translation.status == TranslationStatus.COMPLETED
    assert translation.translation_quality == TranslationQuality.REVIEWED


@pytest.mark.asyncio
async def test_subtitle_style_preset_creation(db_session: AsyncSession):
    """Test SubtitleStylePreset model creation."""
    # Create system preset without user
    preset = SubtitleStylePreset(
        name="YouTube Default",
        description="Professional YouTube-style subtitles",
        platform=Platform.YOUTUBE,
        style_config={
            "font_size": 32,
            "font_color": "#FFFFFF",
            "outline_enabled": True,
        },
        is_system_preset=True,
    )
    db_session.add(preset)
    await db_session.commit()
    await db_session.refresh(preset)

    assert preset.id is not None
    assert preset.name == "YouTube Default"
    assert preset.platform == Platform.YOUTUBE
    assert preset.is_system_preset is True
    assert preset.is_public is True
    assert preset.usage_count == 0
    assert preset.created_by is None


@pytest.mark.asyncio
async def test_subtitle_style_preset_unique_name(db_session: AsyncSession):
    """Test SubtitleStylePreset unique constraint on name."""
    preset1 = SubtitleStylePreset(
        name="TikTok Viral",
        description="TikTok style",
        platform=Platform.TIKTOK,
        style_config={},
    )
    db_session.add(preset1)
    await db_session.commit()

    # Try to create duplicate name
    preset2 = SubtitleStylePreset(
        name="TikTok Viral",
        description="Another TikTok style",
        platform=Platform.TIKTOK,
        style_config={},
    )
    db_session.add(preset2)

    with pytest.raises(IntegrityError):
        await db_session.commit()


@pytest.mark.asyncio
async def test_subtitle_style_preset_custom_by_user(db_session: AsyncSession):
    """Test custom SubtitleStylePreset created by user."""
    user = User(email="test@example.com", hashed_password="hashed")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Create custom preset by user
    preset = SubtitleStylePreset(
        name="My Custom Style",
        description="My personal subtitle style",
        platform=Platform.CUSTOM,
        style_config={
            "font_family": "Comic Sans MS",
            "font_size": 50,
        },
        is_system_preset=False,
        is_public=False,
        created_by=user.id,
    )
    db_session.add(preset)
    await db_session.commit()
    await db_session.refresh(preset)

    assert preset.name == "My Custom Style"
    assert preset.platform == Platform.CUSTOM
    assert preset.is_system_preset is False
    assert preset.is_public is False
    assert preset.created_by == user.id
