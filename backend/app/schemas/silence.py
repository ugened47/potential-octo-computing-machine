"""Silence removal API schemas."""

from typing import Optional

from pydantic import BaseModel, Field


class SilenceRemovalRequest(BaseModel):
    """Silence removal request schema."""

    threshold_db: int = Field(
        default=-40, ge=-60, le=-20, description="Silence threshold in dB"
    )
    min_duration_ms: int = Field(
        default=1000, ge=500, le=5000, description="Minimum silence duration in milliseconds"
    )
    excluded_segments: Optional[list[int]] = Field(
        default=None, description="List of segment indices to exclude from removal"
    )


class SilenceSegment(BaseModel):
    """Silence segment schema."""

    start_time: float
    end_time: float
    duration: float


class SilenceDetectionResponse(BaseModel):
    """Silence detection response schema."""

    segments: list[SilenceSegment]
    total_duration: float
    original_duration: float
    reduction_percentage: float


class SilenceRemovalProgress(BaseModel):
    """Silence removal progress response."""

    video_id: str
    progress: int = Field(..., ge=0, le=100, description="Progress percentage (0-100)")
    status: str = Field(..., description="Current status message")
    estimated_time_remaining: Optional[int] = Field(
        None, description="Estimated seconds remaining"
    )

