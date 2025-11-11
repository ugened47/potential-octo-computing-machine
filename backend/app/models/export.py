"""Video Export models."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.template import SocialMediaTemplate
    from app.models.video import Video


class ExportStatus(str, Enum):
    """Export processing status."""

    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class CropStrategy(str, Enum):
    """Aspect ratio crop strategies."""

    SMART = "smart"
    CENTER = "center"
    LETTERBOX = "letterbox"
    BLUR = "blur"


class VideoExport(SQLModel, table=True):
    """Video export model for tracking social media exports."""

    __tablename__ = "video_exports"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # References
    video_id: UUID = Field(foreign_key="videos.id", index=True)
    template_id: UUID = Field(foreign_key="social_media_templates.id", index=True)

    # Export file metadata
    export_url: str | None = Field(default=None, max_length=500)
    s3_key: str | None = Field(default=None, max_length=500)
    file_size: int | None = Field(default=None)  # Size in bytes
    resolution: str | None = Field(default=None, max_length=20)  # e.g., "1080x1920"
    duration_seconds: float | None = Field(default=None)

    # Export configuration
    segment_start_time: float | None = Field(default=None)
    segment_end_time: float | None = Field(default=None)
    crop_strategy: CropStrategy = Field(default=CropStrategy.SMART)

    # Processing status
    status: ExportStatus = Field(default=ExportStatus.PROCESSING, index=True)
    error_message: str | None = Field(default=None)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = Field(default=None)

    # Relationships
    video: "Video" = Relationship(back_populates="exports")
    template: "SocialMediaTemplate" = Relationship(back_populates="exports")
