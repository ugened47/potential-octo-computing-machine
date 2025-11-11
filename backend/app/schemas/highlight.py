"""Pydantic schemas for highlight detection API."""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class SensitivityLevel(str, Enum):
    """Highlight detection sensitivity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    MAX = "max"


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


class ScoreWeights(BaseModel):
    """Weights for component scores."""

    audio_energy: float = Field(default=0.35, ge=0.0, le=1.0)
    scene_change: float = Field(default=0.20, ge=0.0, le=1.0)
    speech_density: float = Field(default=0.25, ge=0.0, le=1.0)
    keyword: float = Field(default=0.20, ge=0.0, le=1.0)


class HighlightDetectionRequest(BaseModel):
    """Request schema for triggering highlight detection."""

    sensitivity: SensitivityLevel = Field(
        default=SensitivityLevel.MEDIUM,
        description="Detection sensitivity level",
    )
    keywords: list[str] = Field(
        default=[],
        description="Custom keywords to search for",
    )
    score_weights: ScoreWeights | None = Field(
        default=None,
        description="Optional custom score weights",
    )


class HighlightResponse(BaseModel):
    """Response schema for a single highlight."""

    id: UUID
    video_id: UUID
    start_time: float
    end_time: float
    overall_score: int
    audio_energy_score: int
    scene_change_score: int
    speech_density_score: int
    keyword_score: int
    detected_keywords: list[str]
    confidence_level: float | None
    duration_seconds: float | None
    rank: int
    highlight_type: HighlightType
    status: HighlightStatus
    context_before_seconds: float
    context_after_seconds: float
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


class HighlightListResponse(BaseModel):
    """Response schema for list of highlights."""

    highlights: list[HighlightResponse]
    total: int


class HighlightUpdateRequest(BaseModel):
    """Request schema for updating a highlight."""

    rank: int | None = Field(default=None, description="New rank")
    status: HighlightStatus | None = Field(default=None, description="New status")
    start_time: float | None = Field(default=None, description="New start time")
    end_time: float | None = Field(default=None, description="New end time")


class HighlightProgress(BaseModel):
    """Progress information for highlight detection."""

    progress: int = Field(ge=0, le=100, description="Progress percentage")
    status: str = Field(description="Current status message")
    estimated_time_remaining: int | None = Field(
        default=None,
        description="Estimated seconds remaining",
    )
    current_stage: str = Field(description="Current processing stage")


class HighlightDetectionJob(BaseModel):
    """Response schema for highlight detection job."""

    job_id: str
    message: str
