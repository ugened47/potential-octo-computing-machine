"""Pydantic schemas for subtitle-related API requests and responses."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


# Subtitle Style Schemas
class SubtitleStyleBase(BaseModel):
    """Base subtitle style properties."""

    language_code: str = Field(..., max_length=10, description="ISO 639-1 language code")
    font_family: str = Field(default="Arial", max_length=100)
    font_size: int = Field(default=24, ge=12, le=72)
    font_weight: str = Field(default="bold", pattern="^(normal|bold)$")
    font_color: str = Field(default="#FFFFFF", pattern="^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{8})$")
    font_alpha: float = Field(default=1.0, ge=0.0, le=1.0)

    background_enabled: bool = Field(default=True)
    background_color: str = Field(default="#000000", pattern="^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{8})$")
    background_alpha: float = Field(default=0.7, ge=0.0, le=1.0)
    background_padding: int = Field(default=10, ge=0)
    background_radius: int = Field(default=4, ge=0)

    outline_enabled: bool = Field(default=True)
    outline_color: str = Field(default="#000000", pattern="^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{8})$")
    outline_width: int = Field(default=2, ge=0, le=8)

    position_vertical: str = Field(default="bottom", pattern="^(top|center|bottom)$")
    position_horizontal: str = Field(default="center", pattern="^(left|center|right)$")
    margin_vertical: int = Field(default=50, ge=0, le=200)
    margin_horizontal: int = Field(default=40, ge=0, le=200)
    max_width_percent: int = Field(default=80, ge=20, le=100)

    words_per_line: int = Field(default=7, ge=1)
    max_lines: int = Field(default=2, ge=1)
    min_display_duration: float = Field(default=1.0, ge=0.5)
    max_display_duration: float = Field(default=6.0, ge=1.0)

    animation_type: str = Field(default="none", pattern="^(none|fade|slide|pop)$")
    animation_duration: float = Field(default=0.3, ge=0.1, le=2.0)

    preset_name: str | None = Field(default=None, max_length=100)
    is_template: bool = Field(default=False)


class SubtitleStyleCreate(SubtitleStyleBase):
    """Schema for creating a subtitle style."""

    pass


class SubtitleStyleUpdate(BaseModel):
    """Schema for updating a subtitle style (all fields optional)."""

    language_code: str | None = Field(None, max_length=10)
    font_family: str | None = Field(None, max_length=100)
    font_size: int | None = Field(None, ge=12, le=72)
    font_weight: str | None = Field(None, pattern="^(normal|bold)$")
    font_color: str | None = Field(None, pattern="^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{8})$")
    font_alpha: float | None = Field(None, ge=0.0, le=1.0)
    background_enabled: bool | None = None
    background_color: str | None = Field(None, pattern="^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{8})$")
    background_alpha: float | None = Field(None, ge=0.0, le=1.0)
    background_padding: int | None = Field(None, ge=0)
    background_radius: int | None = Field(None, ge=0)
    outline_enabled: bool | None = None
    outline_color: str | None = Field(None, pattern="^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{8})$")
    outline_width: int | None = Field(None, ge=0, le=8)
    position_vertical: str | None = Field(None, pattern="^(top|center|bottom)$")
    position_horizontal: str | None = Field(None, pattern="^(left|center|right)$")
    margin_vertical: int | None = Field(None, ge=0, le=200)
    margin_horizontal: int | None = Field(None, ge=0, le=200)
    max_width_percent: int | None = Field(None, ge=20, le=100)
    words_per_line: int | None = Field(None, ge=1)
    max_lines: int | None = Field(None, ge=1)
    min_display_duration: float | None = Field(None, ge=0.5)
    max_display_duration: float | None = Field(None, ge=1.0)
    animation_type: str | None = Field(None, pattern="^(none|fade|slide|pop)$")
    animation_duration: float | None = Field(None, ge=0.1, le=2.0)
    preset_name: str | None = Field(None, max_length=100)
    is_template: bool | None = None


class SubtitleStyleResponse(SubtitleStyleBase):
    """Schema for subtitle style response."""

    id: UUID
    video_id: UUID
    created_by: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Subtitle Translation Schemas
class TranslationSegment(BaseModel):
    """Schema for a single translation segment."""

    start_time: float
    end_time: float
    original_text: str
    translated_text: str
    confidence: float = Field(ge=0.0, le=1.0)


class SubtitleTranslationCreate(BaseModel):
    """Schema for creating subtitle translations."""

    target_languages: list[str] = Field(..., min_length=1, max_length=10)
    source_language: str | None = None


class SubtitleTranslationResponse(BaseModel):
    """Schema for subtitle translation response."""

    id: UUID
    video_id: UUID
    source_language: str
    target_language: str
    translation_service: str
    translation_quality: str
    segments: dict[str, Any]
    character_count: int
    word_count: int
    status: str
    error_message: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UpdateTranslationSegments(BaseModel):
    """Schema for updating translation segments."""

    segments: list[TranslationSegment]


# Subtitle Style Preset Schemas
class SubtitleStylePresetResponse(BaseModel):
    """Schema for subtitle style preset response."""

    id: UUID
    name: str
    description: str
    platform: str
    thumbnail_url: str | None
    style_config: dict[str, Any]
    usage_count: int
    is_system_preset: bool
    is_public: bool
    created_by: UUID | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ApplyPresetRequest(BaseModel):
    """Schema for applying a preset to a video."""

    preset_name: str
    language: str = Field(default="en", max_length=10)


class CreatePresetRequest(BaseModel):
    """Schema for creating a custom preset from a style."""

    style_id: UUID
    name: str = Field(..., max_length=100)
    description: str = Field(..., max_length=500)
    is_public: bool = Field(default=True)


# Subtitle Burning Schemas
class BurnSubtitlesRequest(BaseModel):
    """Schema for burn subtitles request."""

    language: str = Field(..., max_length=10)
    style_id: UUID | None = None
    output_format: str = Field(default="mp4", pattern="^(mp4|avi|mov)$")


class BurnSubtitlesProgress(BaseModel):
    """Schema for subtitle burning progress."""

    progress: int = Field(ge=0, le=100)
    status: str  # pending, downloading, generating_subtitles, burning, uploading, completed, failed
    estimated_time_remaining: float
    current_stage: str
    error_message: str | None = None


class SubtitledVersion(BaseModel):
    """Schema for a subtitled video version."""

    id: UUID
    video_id: UUID
    language: str
    style_id: UUID
    file_path: str
    file_size: int
    download_url: str
    created_at: datetime


# Preview Schemas
class GeneratePreviewRequest(BaseModel):
    """Schema for generating style preview."""

    sample_text: str = Field(default="Sample subtitle text", max_length=200)


class PreviewResponse(BaseModel):
    """Schema for preview response."""

    preview_url: str
    expires_at: datetime


# Translation Cost Schemas
class TranslationCostEstimate(BaseModel):
    """Schema for translation cost estimate."""

    character_count: int
    cost_per_language: float
    total_cost: float
    currency: str = "USD"
    languages: list[str]


# Language Info Schemas
class LanguageInfo(BaseModel):
    """Schema for language information."""

    code: str
    name: str
    native_name: str
    rtl: bool
    flag_emoji: str | None = None


# Clone Style Schema
class CloneStyleRequest(BaseModel):
    """Schema for cloning a style to another video."""

    target_video_id: UUID
