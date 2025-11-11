"""Video Export schemas for request/response validation."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.models import CropStrategy, ExportStatus


# Request schemas
class ExportCreate(BaseModel):
    """Request schema for creating a video export."""

    template_id: UUID = Field(..., description="Template ID to use for export")
    segment_start_time: float | None = Field(None, ge=0, description="Segment start time in seconds")
    segment_end_time: float | None = Field(None, ge=0, description="Segment end time in seconds")
    crop_strategy: CropStrategy = Field(CropStrategy.SMART, description="Crop strategy")
    enable_captions: bool = Field(True, description="Enable caption overlay")
    quality: str = Field("high", description="Export quality (high, medium, low)")

    @field_validator("segment_end_time")
    @classmethod
    def validate_segment_times(cls, v, values):
        """Validate segment end time is greater than start time."""
        if v is not None and "segment_start_time" in values.data:
            start = values.data.get("segment_start_time")
            if start is not None and v <= start:
                raise ValueError("segment_end_time must be greater than segment_start_time")
        return v


class PreviewCreate(BaseModel):
    """Request schema for generating an export preview."""

    template_id: UUID = Field(..., description="Template ID")
    segment_start_time: float | None = Field(None, ge=0, description="Segment start time")
    segment_end_time: float | None = Field(None, ge=0, description="Segment end time")
    crop_strategy: CropStrategy = Field(CropStrategy.SMART, description="Crop strategy")


# Response schemas
class ExportRead(BaseModel):
    """Response schema for export data."""

    id: UUID
    video_id: UUID
    template_id: UUID
    export_url: str | None
    s3_key: str | None
    file_size: int | None
    resolution: str | None
    duration_seconds: float | None
    segment_start_time: float | None
    segment_end_time: float | None
    crop_strategy: CropStrategy
    status: ExportStatus
    error_message: str | None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None

    class Config:
        """Pydantic config."""

        from_attributes = True


class ExportList(BaseModel):
    """Response schema for export list."""

    exports: list[ExportRead]
    total: int


class ExportProgress(BaseModel):
    """Response schema for export progress."""

    progress: int = Field(..., ge=0, le=100, description="Progress percentage")
    status: ExportStatus
    current_stage: str = Field(..., description="Current processing stage")
    estimated_time_remaining: int | None = Field(None, ge=0, description="Estimated seconds remaining")


class ExportResponse(BaseModel):
    """Response schema for export creation."""

    export_id: UUID
    job_id: str
    message: str


class PreviewResponse(BaseModel):
    """Response schema for preview generation."""

    preview_url: str
    expires_at: datetime
