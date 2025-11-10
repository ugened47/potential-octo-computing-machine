"""Transcript API schemas."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.transcript import TranscriptStatus


class WordTimestamp(BaseModel):
    """Word-level timestamp data."""

    word: str
    start: float = Field(..., description="Start time in seconds")
    end: float = Field(..., description="End time in seconds")
    confidence: float | None = Field(None, description="Confidence score (0-1)")


class TranscriptRead(BaseModel):
    """Transcript read schema."""

    id: UUID
    video_id: UUID
    full_text: str
    word_timestamps: dict[str, Any]
    language: str | None = None
    status: TranscriptStatus
    accuracy_score: float | None = None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None

    class Config:
        """Pydantic config."""

        from_attributes = True


class TranscriptProgress(BaseModel):
    """Transcript progress response."""

    video_id: UUID
    progress: int = Field(..., ge=0, le=100, description="Progress percentage (0-100)")
    status: str = Field(..., description="Current status message")
    estimated_time_remaining: int | None = Field(None, description="Estimated seconds remaining")


class TranscriptExportRequest(BaseModel):
    """Transcript export request."""

    format: str = Field(..., description="Export format: srt or vtt")
