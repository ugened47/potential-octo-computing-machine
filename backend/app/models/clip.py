"""Clip model for video clips."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import ARRAY, Column, String
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.video import Video


class ClipStatus(str, Enum):
    """Clip processing status."""

    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Clip(SQLModel, table=True):
    """Clip model for video segments."""

    __tablename__ = "clips"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    video_id: UUID = Field(foreign_key="videos.id", index=True)

    # Clip metadata
    title: str = Field(max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    keywords: list[str] = Field(
        default_factory=list,
        sa_column=Column(ARRAY(String), nullable=False),
    )

    # Clip timing
    start_time: float = Field(..., description="Start time in seconds")
    end_time: float = Field(..., description="End time in seconds")
    duration: float | None = Field(default=None, description="Duration in seconds")

    # Storage
    clip_url: str | None = Field(
        default=None, max_length=500, description="S3 key or URL for clip"
    )
    status: ClipStatus = Field(default=ClipStatus.PROCESSING)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    video: Optional["Video"] = Relationship()
