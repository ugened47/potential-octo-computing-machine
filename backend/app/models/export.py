"""Export model."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, JSON
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.video import Video


class ExportStatus(str, Enum):
    """Export processing status."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExportType(str, Enum):
    """Type of export operation."""

    SINGLE = "single"  # Single clip export
    COMBINED = "combined"  # Combined/merged clips into one video
    CLIPS = "clips"  # Individual clips as separate files (ZIP)


class Resolution(str, Enum):
    """Video resolution options."""

    R_720P = "720p"
    R_1080P = "1080p"
    R_4K = "4k"


class Format(str, Enum):
    """Video format options."""

    MP4 = "mp4"
    MOV = "mov"
    WEBM = "webm"


class QualityPreset(str, Enum):
    """Video quality presets."""

    HIGH = "high"  # CRF 18, 8Mbps
    MEDIUM = "medium"  # CRF 23, 4Mbps
    LOW = "low"  # CRF 28, 2Mbps


class Export(SQLModel, table=True):
    """Export model for video export jobs."""

    __tablename__ = "exports"

    # Primary key
    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # Foreign keys
    video_id: UUID = Field(foreign_key="videos.id", index=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)

    # Export configuration
    export_type: ExportType = Field(default=ExportType.SINGLE)
    resolution: Resolution = Field(default=Resolution.R_1080P)
    format: Format = Field(default=Format.MP4)
    quality_preset: QualityPreset = Field(default=QualityPreset.MEDIUM)

    # Segment selections (array of {start_time, end_time, clip_id})
    segment_selections: list[dict[str, Any]] | None = Field(
        default=None, sa_column=Column(JSON)
    )

    # Processing status
    status: ExportStatus = Field(default=ExportStatus.PENDING, index=True)
    progress_percentage: int = Field(default=0, ge=0, le=100)
    error_message: str | None = Field(default=None)

    # Output data
    output_s3_key: str | None = Field(default=None, max_length=500)
    output_url: str | None = Field(default=None, max_length=500)
    file_size_bytes: int | None = Field(default=None)
    total_duration_seconds: int | None = Field(default=None)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: datetime | None = Field(default=None)
    completed_at: datetime | None = Field(default=None)

    # Relationships
    video: Optional["Video"] = Relationship(back_populates="exports")
    user: Optional["User"] = Relationship(back_populates="exports")
