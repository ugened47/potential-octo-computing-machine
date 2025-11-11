"""Social Media Template schemas for request/response validation."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models import PlatformType, StylePreset


# Request schemas
class TemplateCreate(BaseModel):
    """Request schema for creating a custom template."""

    name: str = Field(..., max_length=255, description="Template name")
    description: str | None = Field(None, description="Template description")
    platform: PlatformType = Field(..., description="Target platform")
    aspect_ratio: str = Field(..., max_length=20, description="Aspect ratio (e.g., '9:16')")
    max_duration_seconds: int = Field(..., gt=0, le=7200, description="Max duration in seconds")
    auto_captions: bool = Field(True, description="Enable auto-captions")
    caption_style: dict = Field(default_factory=dict, description="Caption style configuration")
    style_preset: StylePreset = Field(StylePreset.MINIMAL, description="Caption style preset")
    video_codec: str = Field("h264", max_length=50, description="Video codec")
    audio_codec: str = Field("aac", max_length=50, description="Audio codec")
    bitrate: str = Field("5M", max_length=20, description="Video bitrate")


class TemplateUpdate(BaseModel):
    """Request schema for updating a template."""

    name: str | None = Field(None, max_length=255, description="Template name")
    description: str | None = Field(None, description="Template description")
    aspect_ratio: str | None = Field(None, max_length=20, description="Aspect ratio")
    max_duration_seconds: int | None = Field(None, gt=0, le=7200, description="Max duration")
    auto_captions: bool | None = Field(None, description="Enable auto-captions")
    caption_style: dict | None = Field(None, description="Caption style configuration")
    style_preset: StylePreset | None = Field(None, description="Caption style preset")
    video_codec: str | None = Field(None, max_length=50, description="Video codec")
    audio_codec: str | None = Field(None, max_length=50, description="Audio codec")
    bitrate: str | None = Field(None, max_length=20, description="Video bitrate")
    is_active: bool | None = Field(None, description="Template active status")


# Response schemas
class TemplateRead(BaseModel):
    """Response schema for template data."""

    id: UUID
    name: str
    description: str | None
    platform: PlatformType
    aspect_ratio: str
    max_duration_seconds: int
    auto_captions: bool
    caption_style: dict
    style_preset: StylePreset
    video_codec: str
    audio_codec: str
    bitrate: str
    is_system_preset: bool
    user_id: UUID | None
    is_active: bool
    usage_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


class TemplateList(BaseModel):
    """Response schema for template list."""

    templates: list[TemplateRead]
    total: int
