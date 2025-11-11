"""Pydantic schemas for Advanced Editor."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.models import (
    AssetType,
    BlendMode,
    ItemType,
    ProjectStatus,
    SourceType,
    TrackType,
    TransitionType,
)


# Project Schemas
class ProjectCreate(BaseModel):
    """Schema for creating a project."""

    name: str = Field(..., max_length=255)
    description: str | None = None
    video_id: UUID | None = None
    width: int = 1920
    height: int = 1080
    frame_rate: float = 30.0
    duration_seconds: float = 60.0
    background_color: str = "#000000"


class ProjectUpdate(BaseModel):
    """Schema for updating a project."""

    name: str | None = None
    description: str | None = None
    width: int | None = None
    height: int | None = None
    frame_rate: float | None = None
    duration_seconds: float | None = None
    background_color: str | None = None
    canvas_settings: dict | None = None
    export_settings: dict | None = None


class ProjectRead(BaseModel):
    """Schema for reading a project."""

    id: UUID
    user_id: UUID
    name: str
    description: str | None
    video_id: UUID | None
    width: int
    height: int
    frame_rate: float
    duration_seconds: float
    background_color: str
    canvas_settings: dict
    export_settings: dict
    thumbnail_url: str | None
    status: ProjectStatus
    last_rendered_at: datetime | None
    render_output_url: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RenderConfig(BaseModel):
    """Schema for render configuration."""

    quality: str = Field(default="high", pattern="^(low|medium|high|max)$")
    format: str = Field(default="mp4", pattern="^(mp4|mov|webm)$")
    resolution: dict | None = None


class RenderProgress(BaseModel):
    """Schema for render progress."""

    progress: int = Field(..., ge=0, le=100)
    stage: str
    status: str
    estimated_time_remaining: float | None = None
    error: str | None = None


class ValidationResult(BaseModel):
    """Schema for project validation result."""

    valid: bool
    errors: list[str]
    warnings: list[str]


# Track Schemas
class TrackCreate(BaseModel):
    """Schema for creating a track."""

    track_type: TrackType
    name: str = Field(..., max_length=255)
    z_index: int | None = None
    volume: float = Field(default=1.0, ge=0.0, le=1.0)
    opacity: float = Field(default=1.0, ge=0.0, le=1.0)


class TrackUpdate(BaseModel):
    """Schema for updating a track."""

    name: str | None = None
    z_index: int | None = None
    is_locked: bool | None = None
    is_visible: bool | None = None
    is_muted: bool | None = None
    volume: float | None = Field(default=None, ge=0.0, le=1.0)
    opacity: float | None = Field(default=None, ge=0.0, le=1.0)
    blend_mode: BlendMode | None = None
    track_order: int | None = None


class TrackRead(BaseModel):
    """Schema for reading a track."""

    id: UUID
    project_id: UUID
    track_type: TrackType
    name: str
    z_index: int
    is_locked: bool
    is_visible: bool
    is_muted: bool
    volume: float
    opacity: float
    blend_mode: BlendMode
    track_order: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# TrackItem Schemas
class TrackItemCreate(BaseModel):
    """Schema for creating a track item."""

    item_type: ItemType
    source_type: SourceType
    source_id: UUID | None = None
    source_url: str | None = None
    start_time: float = Field(..., ge=0.0)
    end_time: float = Field(..., ge=0.0)
    trim_start: float = Field(default=0.0, ge=0.0)
    trim_end: float = Field(default=0.0, ge=0.0)
    position_x: float = Field(default=0.0, ge=0.0, le=1.0)
    position_y: float = Field(default=0.0, ge=0.0, le=1.0)
    scale_x: float = Field(default=1.0, ge=0.0)
    scale_y: float = Field(default=1.0, ge=0.0)
    rotation: float = Field(default=0.0)
    crop_settings: dict | None = None
    transform_settings: dict | None = None
    text_content: str | None = None
    text_style: dict | None = None
    effects: list | None = None
    transition_in_id: UUID | None = None
    transition_out_id: UUID | None = None


class TrackItemUpdate(BaseModel):
    """Schema for updating a track item."""

    item_type: ItemType | None = None
    source_type: SourceType | None = None
    source_id: UUID | None = None
    source_url: str | None = None
    start_time: float | None = Field(default=None, ge=0.0)
    end_time: float | None = Field(default=None, ge=0.0)
    trim_start: float | None = Field(default=None, ge=0.0)
    trim_end: float | None = Field(default=None, ge=0.0)
    position_x: float | None = Field(default=None, ge=0.0, le=1.0)
    position_y: float | None = Field(default=None, ge=0.0, le=1.0)
    scale_x: float | None = Field(default=None, ge=0.0)
    scale_y: float | None = Field(default=None, ge=0.0)
    rotation: float | None = None
    crop_settings: dict | None = None
    transform_settings: dict | None = None
    text_content: str | None = None
    text_style: dict | None = None
    effects: list | None = None
    transition_in_id: UUID | None = None
    transition_out_id: UUID | None = None


class TrackItemRead(BaseModel):
    """Schema for reading a track item."""

    id: UUID
    track_id: UUID
    item_type: ItemType
    source_type: SourceType
    source_id: UUID | None
    source_url: str | None
    start_time: float
    end_time: float
    duration: float
    trim_start: float
    trim_end: float
    position_x: float
    position_y: float
    scale_x: float
    scale_y: float
    rotation: float
    crop_settings: dict | None
    transform_settings: dict | None
    text_content: str | None
    text_style: dict | None
    effects: list | None
    transition_in_id: UUID | None
    transition_out_id: UUID | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SplitItemRequest(BaseModel):
    """Schema for splitting a track item."""

    split_time: float = Field(..., gt=0.0)


class SplitItemResponse(BaseModel):
    """Schema for split item response."""

    item1: TrackItemRead
    item2: TrackItemRead


# Asset Schemas
class AssetCreate(BaseModel):
    """Schema for creating an asset (used with multipart form data)."""

    asset_type: AssetType
    name: str = Field(..., max_length=255)
    tags: list[str] = Field(default_factory=list)


class AssetUpdate(BaseModel):
    """Schema for updating an asset."""

    name: str | None = Field(default=None, max_length=255)
    tags: list[str] | None = None


class AssetRead(BaseModel):
    """Schema for reading an asset."""

    id: UUID
    user_id: UUID
    asset_type: AssetType
    name: str
    file_url: str
    file_size: int | None
    mime_type: str | None
    width: int | None
    height: int | None
    duration_seconds: float | None
    metadata: dict
    thumbnail_url: str | None
    is_public: bool
    tags: list[str]
    usage_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Transition Schemas
class TransitionRead(BaseModel):
    """Schema for reading a transition."""

    id: UUID
    name: str
    transition_type: TransitionType
    direction: str | None
    default_duration: float
    parameters: dict
    preview_url: str | None
    is_builtin: bool
    is_public: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TransitionCreate(BaseModel):
    """Schema for creating a custom transition."""

    name: str = Field(..., max_length=255)
    transition_type: TransitionType
    direction: str | None = None
    default_duration: float = Field(default=0.5, gt=0.0)
    parameters: dict = Field(default_factory=dict)
