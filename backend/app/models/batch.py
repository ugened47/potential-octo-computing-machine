"""Batch processing models."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlmodel import JSON, Column, Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.video import Video


class BatchJobStatus(str, Enum):
    """Batch job processing status."""

    PENDING = "pending"
    PROCESSING = "processing"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BatchVideoStatus(str, Enum):
    """Batch video processing status."""

    PENDING = "pending"
    UPLOADING = "uploading"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ProcessingStage(str, Enum):
    """Video processing stage."""

    UPLOADING = "uploading"
    TRANSCRIBING = "transcribing"
    REMOVING_SILENCE = "removing_silence"
    DETECTING_HIGHLIGHTS = "detecting_highlights"
    EXPORTING = "exporting"


class BatchJob(SQLModel, table=True):
    """Batch job model for processing multiple videos with shared settings."""

    __tablename__ = "batch_jobs"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    name: str = Field(max_length=100)
    description: str | None = Field(default=None)

    # Processing settings stored as JSONB
    settings: dict = Field(default_factory=dict, sa_column=Column(JSON))

    # Status tracking
    status: BatchJobStatus = Field(default=BatchJobStatus.PENDING, index=True)

    # Progress metrics
    total_videos: int = Field(default=0)
    completed_videos: int = Field(default=0)
    failed_videos: int = Field(default=0)
    cancelled_videos: int = Field(default=0)

    # Statistics
    total_duration_seconds: float = Field(default=0.0)
    processed_duration_seconds: float = Field(default=0.0)
    estimated_time_remaining: int | None = Field(default=None)  # in seconds

    # Priority (0-10, higher = more priority)
    priority: int = Field(default=5, ge=0, le=10)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    started_at: datetime | None = Field(default=None)
    completed_at: datetime | None = Field(default=None)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    videos: list["BatchVideo"] = Relationship(back_populates="batch_job")


class BatchVideo(SQLModel, table=True):
    """Batch video model representing a video in a batch job."""

    __tablename__ = "batch_videos"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    batch_job_id: UUID = Field(foreign_key="batch_jobs.id", index=True)
    video_id: UUID = Field(foreign_key="videos.id", index=True)
    position: int = Field(index=True)  # Order in batch

    # Status tracking
    status: BatchVideoStatus = Field(default=BatchVideoStatus.PENDING, index=True)
    progress_percentage: int = Field(default=0, ge=0, le=100)
    current_stage: ProcessingStage | None = Field(default=None)

    # Error tracking
    error_message: str | None = Field(default=None)
    retry_count: int = Field(default=0)
    max_retries: int = Field(default=3)

    # Processing results stored as JSONB
    processing_result: dict | None = Field(default=None, sa_column=Column(JSON))
    output_video_url: str | None = Field(default=None, max_length=500)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: datetime | None = Field(default=None)
    completed_at: datetime | None = Field(default=None)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    batch_job: Optional["BatchJob"] = Relationship(back_populates="videos")
    video: Optional["Video"] = Relationship()
