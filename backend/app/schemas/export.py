"""Export schemas for request/response validation."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.models import ExportStatus, ExportType, Format, QualityPreset, Resolution


# Request schemas
class ExportSegmentInput(BaseModel):
    """Schema for segment selection in export request."""

    start_time: float = Field(..., ge=0, description="Start time in seconds")
    end_time: float = Field(..., gt=0, description="End time in seconds")
    clip_id: UUID | None = Field(None, description="Optional clip ID reference")


class ExportCreateRequest(BaseModel):
    """Request schema for creating a new export job."""

    export_type: ExportType = Field(
        ..., description="Type of export: single, combined, or clips"
    )
    resolution: Resolution = Field(..., description="Output video resolution")
    format: Format = Field(..., description="Output video format")
    quality_preset: QualityPreset = Field(..., description="Quality preset")
    segments: list[ExportSegmentInput] = Field(
        ..., min_length=1, description="Segments to export"
    )


class ExportProgressResponse(BaseModel):
    """Response schema for export progress data."""

    export_id: UUID = Field(..., description="Export ID")
    status: ExportStatus = Field(..., description="Current export status")
    progress_percentage: int = Field(..., ge=0, le=100, description="Progress (0-100)")
    current_stage: str | None = Field(
        None, description="Current processing stage description"
    )
    estimated_time_remaining: int | None = Field(
        None, description="Estimated time remaining in seconds"
    )
    elapsed_time: int | None = Field(None, description="Elapsed time in seconds")


class ExportDownloadResponse(BaseModel):
    """Response schema for export download URL."""

    url: str = Field(..., description="Presigned download URL")
    expires_at: datetime = Field(..., description="URL expiration timestamp")
    file_size_bytes: int | None = Field(None, description="File size in bytes")


# Response schemas
class ExportRead(BaseModel):
    """Response schema for export data."""

    id: UUID
    video_id: UUID
    user_id: UUID
    export_type: ExportType
    resolution: Resolution
    format: Format
    quality_preset: QualityPreset
    segment_selections: list[dict[str, Any]] | None
    status: ExportStatus
    progress_percentage: int
    error_message: str | None
    output_s3_key: str | None
    output_url: str | None
    file_size_bytes: int | None
    total_duration_seconds: int | None
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None
    completed_at: datetime | None

    class Config:
        """Pydantic config."""

        from_attributes = True


class ExportListResponse(BaseModel):
    """Response schema for paginated export list."""

    exports: list[ExportRead] = Field(..., description="List of exports")
    total: int = Field(..., description="Total number of exports")
    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Items per page")
    has_more: bool = Field(..., description="Whether there are more pages")
