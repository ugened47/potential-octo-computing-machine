"""Video Export model."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.template import SocialMediaTemplate
    from app.models.video import Video


class ExportStatus(str, Enum):
    """Video export status."""

    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class CropStrategy(str, Enum):
    """Aspect ratio crop/transform strategies."""

    SMART = "smart"  # Smart crop with face/motion detection
    CENTER = "center"  # Simple center crop
    LETTERBOX = "letterbox"  # Add letterbox bars
    BLUR = "blur"  # Blur background with scaled video


class VideoExport(SQLModel, table=True):
    """Video export model for tracking social media exports."""

    __tablename__ = "video_exports"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # Foreign keys
    video_id: UUID = Field(foreign_key="videos.id", index=True)
    template_id: UUID = Field(foreign_key="social_media_templates.id", index=True)

    # Export output
    export_url: str | None = Field(default=None, max_length=500)
    status: ExportStatus = Field(default=ExportStatus.PROCESSING, index=True)

    # File metadata
    file_size: int | None = Field(default=None)  # in bytes
    resolution: str | None = Field(default=None, max_length=20)  # e.g., "1080x1920"
    duration_seconds: float | None = Field(default=None)

    # Export configuration
    segment_start_time: float | None = Field(default=None)  # in seconds
    segment_end_time: float | None = Field(default=None)  # in seconds
    crop_strategy: CropStrategy = Field(default=CropStrategy.BLUR)

    # Error handling
    error_message: str | None = Field(default=None)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = Field(default=None)

    # Relationships
    video: Optional["Video"] = Relationship()
    template: Optional["SocialMediaTemplate"] = Relationship()
