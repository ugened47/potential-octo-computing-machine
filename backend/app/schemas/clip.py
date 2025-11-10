"""Clip API schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.clip import ClipStatus


class ClipCreate(BaseModel):
    """Clip creation schema."""

    video_id: UUID
    start_time: float = Field(..., ge=0, description="Start time in seconds")
    end_time: float = Field(..., gt=0, description="End time in seconds")
    title: str = Field(..., max_length=255)
    description: str | None = Field(None, max_length=1000)
    keywords: list[str] = Field(default_factory=list)


class ClipRead(BaseModel):
    """Clip read schema."""

    id: UUID
    video_id: UUID
    title: str
    description: str | None = None
    keywords: list[str]
    start_time: float
    end_time: float
    duration: float | None = None
    clip_url: str | None = None
    status: ClipStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


class ClipProgress(BaseModel):
    """Clip generation progress response."""

    clip_id: UUID
    progress: int = Field(..., ge=0, le=100, description="Progress percentage (0-100)")
    status: str = Field(..., description="Current status message")
    estimated_time_remaining: int | None = Field(None, description="Estimated seconds remaining")


class SearchRequest(BaseModel):
    """Search request schema."""

    keywords: list[str] = Field(..., min_items=1, description="Keywords to search for")
    padding_seconds: float = Field(
        default=5.0, ge=0, le=30, description="Padding around matches in seconds"
    )


class SearchResult(BaseModel):
    """Search result schema."""

    id: str
    start_time: float
    end_time: float
    transcript_excerpt: str
    relevance_score: float
    matched_keywords: list[str]
