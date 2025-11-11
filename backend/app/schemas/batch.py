"""Batch processing schemas for request/response validation."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.batch import BatchJobStatus, BatchVideoStatus, ProcessingStage


# Settings schemas
class BatchSettings(BaseModel):
    """Batch processing settings."""

    transcribe: bool = Field(default=False, description="Enable transcription")
    remove_silence: bool = Field(default=False, description="Enable silence removal")
    detect_highlights: bool = Field(default=False, description="Enable highlight detection")
    silence_threshold: float = Field(default=-40.0, ge=-60.0, le=-20.0, description="Silence threshold in dB")
    highlight_sensitivity: str = Field(default="medium", description="Highlight detection sensitivity (low, medium, high, max)")
    export_format: str = Field(default="mp4", description="Export format (mp4, mov, webm)")
    export_quality: str = Field(default="1080p", description="Export quality (720p, 1080p, 4K)")
    language: str | None = Field(default="en", description="Transcription language")
    keywords: list[str] = Field(default_factory=list, description="Custom keywords for highlight detection")


# Request schemas
class BatchJobCreate(BaseModel):
    """Request schema for creating a batch job."""

    name: str = Field(..., max_length=100, description="Batch job name")
    description: str | None = Field(None, description="Batch job description")
    settings: BatchSettings = Field(..., description="Processing settings for all videos")
    video_count: int = Field(..., ge=1, le=50, description="Number of videos in batch")


class AddVideosRequest(BaseModel):
    """Request schema for adding videos to existing batch."""

    video_ids: list[UUID] = Field(..., min_length=1, description="List of video IDs to add")


class BatchExportRequest(BaseModel):
    """Request schema for batch export."""

    format: str = Field(..., description="Export format (zip, merged, playlist)")
    include_failed: bool = Field(default=False, description="Include failed videos in export")
    custom_naming: str | None = Field(None, description="Custom naming pattern for files")


# Response schemas
class BatchVideoResponse(BaseModel):
    """Response schema for batch video data."""

    id: UUID
    batch_job_id: UUID
    video_id: UUID
    position: int
    status: BatchVideoStatus
    progress_percentage: int
    current_stage: ProcessingStage | None
    error_message: str | None
    retry_count: int
    max_retries: int
    processing_result: dict | None
    output_video_url: str | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    updated_at: datetime

    class Config:
        from_attributes = True


class BatchJobResponse(BaseModel):
    """Response schema for batch job data."""

    id: UUID
    user_id: UUID
    name: str
    description: str | None
    settings: dict
    status: BatchJobStatus
    total_videos: int
    completed_videos: int
    failed_videos: int
    cancelled_videos: int
    total_duration_seconds: float
    processed_duration_seconds: float
    estimated_time_remaining: int | None
    priority: int
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    updated_at: datetime
    videos: list[BatchVideoResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True


class BatchJobListResponse(BaseModel):
    """Response schema for batch job list."""

    batch_jobs: list[BatchJobResponse]
    total: int
    limit: int
    offset: int


class BatchJobCreateResponse(BaseModel):
    """Response schema for batch job creation."""

    batch_job: BatchJobResponse
    upload_urls: list[str] = Field(..., description="Presigned URLs for video uploads")


class BatchJobStartResponse(BaseModel):
    """Response schema for starting batch processing."""

    job_id: str = Field(..., description="ARQ job ID for tracking")
    batch_job: BatchJobResponse


class BatchExportResponse(BaseModel):
    """Response schema for batch export."""

    export_job_id: str = Field(..., description="Export job ID for tracking")
    status: str = Field(..., description="Export status (pending, processing, completed, failed)")
    progress: int = Field(default=0, ge=0, le=100, description="Export progress percentage")
    download_url: str | None = Field(None, description="Download URL when export is completed")
    file_size: int | None = Field(None, description="Export file size in bytes")
    expires_at: datetime | None = Field(None, description="Download URL expiration time")


class BatchProgressEvent(BaseModel):
    """Real-time progress event schema."""

    type: str = Field(..., description="Event type (progress, video_started, video_completed, video_failed, batch_completed)")
    batch_job_id: UUID
    video_id: UUID | None = Field(None, description="Video ID if event is video-specific")
    progress: int = Field(..., ge=0, le=100, description="Progress percentage")
    current_stage: ProcessingStage | None = Field(None, description="Current processing stage")
    message: str | None = Field(None, description="Event message")
    completed_count: int = Field(default=0, description="Number of completed videos")
    failed_count: int = Field(default=0, description="Number of failed videos")
    pending_count: int = Field(default=0, description="Number of pending videos")
    estimated_time_remaining: int | None = Field(None, description="Estimated time remaining in seconds")


class UploadProgress(BaseModel):
    """Upload progress tracking schema."""

    file_index: int = Field(..., description="Index of the file being uploaded")
    file_name: str = Field(..., description="Name of the file")
    progress: int = Field(..., ge=0, le=100, description="Upload progress percentage")
    status: str = Field(..., description="Upload status (pending, uploading, completed, failed)")
    error: str | None = Field(None, description="Error message if upload failed")
