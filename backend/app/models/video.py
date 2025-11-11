"""Video model."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.export import VideoExport
    from app.models.transcript import Transcript


class VideoStatus(str, Enum):
    """Video processing status."""

    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Video(SQLModel, table=True):
    """Video model."""

    __tablename__ = "videos"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    title: str = Field(max_length=255)
    description: str | None = Field(default=None)

    # File metadata
    file_size: int | None = Field(default=None)
    format: str | None = Field(default=None, max_length=50)
    duration: float | None = Field(default=None)  # Duration in seconds
    resolution: str | None = Field(default=None, max_length=20)  # e.g., "1920x1080"
    s3_key: str | None = Field(default=None, max_length=500)
    cloudfront_url: str | None = Field(default=None, max_length=500)
    thumbnail_url: str | None = Field(default=None, max_length=500)

    # Processing status
    status: VideoStatus = Field(default=VideoStatus.UPLOADED)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    transcript: Optional["Transcript"] = Relationship(back_populates="video")
    exports: list["VideoExport"] = Relationship(back_populates="video")
