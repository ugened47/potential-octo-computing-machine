"""Transcript model."""

from datetime import datetime
from enum import Enum
from typing import Any, Optional, TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Column, JSON
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.video import Video


class TranscriptStatus(str, Enum):
    """Transcript processing status."""

    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Transcript(SQLModel, table=True):
    """Transcript model with word-level timestamps."""

    __tablename__ = "transcripts"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    video_id: UUID = Field(foreign_key="videos.id", index=True)
    
    # Transcript content
    full_text: str = Field(index=True)  # Full-text search index will be added in migration
    word_timestamps: dict[str, Any] = Field(
        default={},
        sa_column=Column(JSON, nullable=False),
    )
    
    # Metadata
    language: Optional[str] = Field(default=None, max_length=10)  # ISO 639-1 code
    status: TranscriptStatus = Field(default=TranscriptStatus.PROCESSING)
    accuracy_score: Optional[float] = Field(default=None)  # Optional confidence score
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(default=None)
    
    # Relationships
    video: Optional["Video"] = Relationship(back_populates="transcript")

