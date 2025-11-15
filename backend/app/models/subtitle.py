"""Subtitle models for styling, translation, and presets."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional
from uuid import UUID, uuid4

from sqlalchemy import JSON, Column
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.video import Video


class PositionVertical(str, Enum):
    """Vertical position options for subtitles."""

    TOP = "top"
    CENTER = "center"
    BOTTOM = "bottom"


class PositionHorizontal(str, Enum):
    """Horizontal position options for subtitles."""

    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"


class FontWeight(str, Enum):
    """Font weight options."""

    NORMAL = "normal"
    BOLD = "bold"


class AnimationType(str, Enum):
    """Animation type options for subtitles."""

    NONE = "none"
    FADE = "fade"
    SLIDE = "slide"
    POP = "pop"


class SubtitleStyle(SQLModel, table=True):
    """
    Subtitle styling configuration for video subtitles.

    Stores all styling properties including font, background, outline,
    position, timing, and animation settings for subtitles.
    """

    __tablename__ = "subtitle_styles"

    # Primary fields
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    video_id: UUID = Field(foreign_key="videos.id", index=True)
    language_code: str = Field(max_length=10, index=True)  # ISO 639-1 format

    # Font properties
    font_family: str = Field(default="Arial", max_length=100)
    font_size: int = Field(default=24, ge=12, le=72)  # Range: 12-72 pixels
    font_weight: FontWeight = Field(default=FontWeight.BOLD)
    font_color: str = Field(default="#FFFFFF", max_length=9)  # Hex format
    font_alpha: float = Field(default=1.0, ge=0.0, le=1.0)  # Range: 0.0-1.0

    # Background properties
    background_enabled: bool = Field(default=True)
    background_color: str = Field(default="#000000", max_length=9)  # Hex format
    background_alpha: float = Field(default=0.7, ge=0.0, le=1.0)
    background_padding: int = Field(default=10, ge=0)
    background_radius: int = Field(default=4, ge=0)

    # Outline/stroke properties
    outline_enabled: bool = Field(default=True)
    outline_color: str = Field(default="#000000", max_length=9)  # Hex format
    outline_width: int = Field(default=2, ge=0, le=8)  # Range: 0-8 pixels

    # Position properties
    position_vertical: PositionVertical = Field(default=PositionVertical.BOTTOM)
    position_horizontal: PositionHorizontal = Field(default=PositionHorizontal.CENTER)
    margin_vertical: int = Field(default=50, ge=0, le=200)  # Range: 0-200 pixels
    margin_horizontal: int = Field(default=40, ge=0, le=200)  # Range: 0-200 pixels
    max_width_percent: int = Field(default=80, ge=20, le=100)  # Range: 20-100%

    # Timing properties
    words_per_line: int = Field(default=7, ge=1)
    max_lines: int = Field(default=2, ge=1)
    min_display_duration: float = Field(default=1.0, ge=0.5)
    max_display_duration: float = Field(default=6.0, ge=1.0)

    # Animation properties
    animation_type: AnimationType = Field(default=AnimationType.NONE)
    animation_duration: float = Field(default=0.3, ge=0.1, le=2.0)

    # Metadata
    preset_name: str | None = Field(default=None, max_length=100, index=True)
    is_template: bool = Field(default=False)
    created_by: UUID = Field(foreign_key="users.id")

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    video: Optional["Video"] = Relationship(back_populates="subtitle_styles")


class TranslationQuality(str, Enum):
    """Translation quality levels."""

    MACHINE = "machine"
    REVIEWED = "reviewed"
    PROFESSIONAL = "professional"


class TranslationStatus(str, Enum):
    """Translation processing status."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class SubtitleTranslation(SQLModel, table=True):
    """
    Translated subtitle content for videos.

    Stores machine or manual translations of video subtitles
    with segment-level translation data and metadata.
    """

    __tablename__ = "subtitle_translations"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    video_id: UUID = Field(foreign_key="videos.id", index=True)
    source_language: str = Field(max_length=10)  # ISO 639-1
    target_language: str = Field(max_length=10, index=True)  # ISO 639-1

    # Translation metadata
    translation_service: str = Field(default="google", max_length=50)
    translation_quality: TranslationQuality = Field(default=TranslationQuality.MACHINE)

    # Translation content - JSONB array of segments
    # Format: [{start_time, end_time, original_text, translated_text, confidence}]
    segments: dict[str, Any] = Field(
        default={},
        sa_column=Column(JSON, nullable=False),
    )

    # Statistics
    character_count: int = Field(default=0)
    word_count: int = Field(default=0)

    # Status and error tracking
    status: TranslationStatus = Field(default=TranslationStatus.PENDING, index=True)
    error_message: str | None = Field(default=None)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    video: Optional["Video"] = Relationship(back_populates="subtitle_translations")


class Platform(str, Enum):
    """Platform types for subtitle presets."""

    YOUTUBE = "youtube"
    TIKTOK = "tiktok"
    INSTAGRAM = "instagram"
    LINKEDIN = "linkedin"
    CUSTOM = "custom"


class SubtitleStylePreset(SQLModel, table=True):
    """
    Reusable subtitle style templates.

    Predefined and custom subtitle styles that can be applied
    to videos for consistent branding across platforms.
    """

    __tablename__ = "subtitle_style_presets"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(unique=True, max_length=100, index=True)
    description: str = Field(max_length=500)
    platform: Platform = Field(default=Platform.CUSTOM, index=True)

    # Preview image
    thumbnail_url: str | None = Field(default=None, max_length=500)

    # Style configuration - JSONB object with all SubtitleStyle properties
    style_config: dict[str, Any] = Field(
        default={},
        sa_column=Column(JSON, nullable=False),
    )

    # Metadata
    usage_count: int = Field(default=0)
    is_system_preset: bool = Field(default=False)
    is_public: bool = Field(default=True, index=True)
    created_by: UUID | None = Field(default=None, foreign_key="users.id")

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    creator: Optional["User"] = Relationship()
