"""Highlight model for AI-powered video highlight detection."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import JSON, Column
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.video import Video


class HighlightType(str, Enum):
    """Type of highlight detected."""

    HIGH_ENERGY = "high_energy"
    KEY_MOMENT = "key_moment"
    KEYWORD_MATCH = "keyword_match"
    SCENE_CHANGE = "scene_change"


class HighlightStatus(str, Enum):
    """Highlight processing and review status."""

    DETECTED = "detected"
    REVIEWED = "reviewed"
    EXPORTED = "exported"
    REJECTED = "rejected"


class Highlight(SQLModel, table=True):
    """
    Highlight model for storing AI-detected video highlights.

    Highlights are automatically detected video segments with high engagement
    potential based on multi-factor scoring (audio, video, speech, keywords).
    """

    __tablename__ = "highlights"

    # Primary key
    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # Foreign key to video
    video_id: UUID = Field(foreign_key="videos.id", index=True)

    # Time range (in seconds)
    start_time: float = Field(ge=0.0)  # Greater than or equal to 0
    end_time: float = Field(ge=0.0)  # Greater than or equal to 0

    # Overall score (0-100)
    overall_score: int = Field(ge=0, le=100, index=True)

    # Component scores (0-100)
    audio_energy_score: int = Field(ge=0, le=100)
    scene_change_score: int = Field(ge=0, le=100)
    speech_density_score: int = Field(ge=0, le=100)
    keyword_score: int = Field(ge=0, le=100)

    # Metadata
    detected_keywords: list[str] = Field(
        default=[],
        sa_column=Column(JSON, nullable=False),
    )
    confidence_level: float | None = Field(default=None, ge=0.0, le=1.0)
    duration_seconds: float | None = Field(default=None, ge=0.0)

    # Ranking (1 = best highlight)
    rank: int = Field(ge=1, index=True)

    # Type and status
    highlight_type: HighlightType = Field(default=HighlightType.KEY_MOMENT)
    status: HighlightStatus = Field(
        default=HighlightStatus.DETECTED,
        index=True,
    )

    # Context padding (seconds to include before/after highlight)
    context_before_seconds: float = Field(default=2.0, ge=0.0)
    context_after_seconds: float = Field(default=3.0, ge=0.0)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    video: Optional["Video"] = Relationship(back_populates="highlights")
