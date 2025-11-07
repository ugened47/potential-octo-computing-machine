"""Video model."""

from datetime import datetime
from enum import Enum
from typing import Optional, TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
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
    description: Optional[str] = Field(default=None)
    
    # File metadata
    file_size: Optional[int] = Field(default=None)
    format: Optional[str] = Field(default=None, max_length=50)
    duration: Optional[float] = Field(default=None)  # Duration in seconds
    resolution: Optional[str] = Field(default=None, max_length=20)  # e.g., "1920x1080"
    s3_key: Optional[str] = Field(default=None, max_length=500)
    cloudfront_url: Optional[str] = Field(default=None, max_length=500)
    thumbnail_url: Optional[str] = Field(default=None, max_length=500)
    
    # Processing status
    status: VideoStatus = Field(default=VideoStatus.UPLOADED)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    transcript: Optional["Transcript"] = Relationship(back_populates="video")

