"""Social Media Template model."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional
from uuid import UUID, uuid4

from sqlmodel import Column, Field, Relationship, SQLModel
from sqlalchemy import JSON

if TYPE_CHECKING:
    from app.models.user import User


class PlatformType(str, Enum):
    """Social media platform types."""

    YOUTUBE_SHORTS = "youtube_shorts"
    TIKTOK = "tiktok"
    INSTAGRAM_REELS = "instagram_reels"
    TWITTER = "twitter"
    LINKEDIN = "linkedin"
    CUSTOM = "custom"


class StylePreset(str, Enum):
    """Caption style presets."""

    MINIMAL = "minimal"
    BOLD = "bold"
    GAMING = "gaming"
    PODCAST = "podcast"
    VLOG = "vlog"
    PROFESSIONAL = "professional"
    TRENDY = "trendy"
    CUSTOM = "custom"


class SocialMediaTemplate(SQLModel, table=True):
    """Social media template model for platform-specific exports."""

    __tablename__ = "social_media_templates"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # Template identification
    name: str = Field(max_length=100)
    description: str | None = Field(default=None)
    platform: PlatformType = Field(index=True)

    # Video configuration
    aspect_ratio: str = Field(max_length=20)  # e.g., "9:16", "16:9", "1:1"
    max_duration_seconds: int = Field(gt=0)

    # Caption configuration
    auto_captions: bool = Field(default=True)
    caption_style: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))
    style_preset: StylePreset = Field(default=StylePreset.MINIMAL)

    # Encoding settings
    video_codec: str = Field(default="h264", max_length=50)
    audio_codec: str = Field(default="aac", max_length=50)
    bitrate: str = Field(default="5M", max_length=20)

    # Template metadata
    is_system_preset: bool = Field(default=False, index=True)
    user_id: UUID | None = Field(default=None, foreign_key="users.id", index=True)
    is_active: bool = Field(default=True, index=True)
    usage_count: int = Field(default=0)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    user: Optional["User"] = Relationship()
