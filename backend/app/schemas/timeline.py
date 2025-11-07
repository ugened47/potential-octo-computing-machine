"""Timeline schemas for waveform and segments."""

from typing import Optional

from pydantic import BaseModel, Field


class WaveformData(BaseModel):
    """Waveform data schema."""

    peaks: list[float] = Field(..., description="Waveform peaks (normalized 0.0-1.0)")
    duration: float = Field(..., description="Video duration in seconds")
    sample_rate: int = Field(default=44100, description="Audio sample rate")


class WaveformStatus(BaseModel):
    """Waveform generation status schema."""

    status: str = Field(..., description="Status: processing, completed, or failed")
    progress: Optional[int] = Field(
        default=None, ge=0, le=100, description="Progress percentage (0-100)"
    )


class Segment(BaseModel):
    """Segment schema."""

    id: str = Field(..., description="Segment ID")
    start_time: float = Field(..., ge=0, description="Start time in seconds")
    end_time: float = Field(..., ge=0, description="End time in seconds")
    selected: bool = Field(default=True, description="Whether segment is selected")


class SegmentCreate(BaseModel):
    """Segment creation schema."""

    id: str = Field(..., description="Segment ID")
    start_time: float = Field(..., ge=0, description="Start time in seconds")
    end_time: float = Field(..., ge=0, description="End time in seconds")
    selected: bool = Field(default=True, description="Whether segment is selected")

