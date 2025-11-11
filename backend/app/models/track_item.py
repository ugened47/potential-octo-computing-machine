"""TrackItem model for Advanced Editor."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Column, Field, JSON, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.track import Track
    from app.models.transition import Transition


class ItemType(str, Enum):
    """Item type."""

    VIDEO_CLIP = "video_clip"
    AUDIO_CLIP = "audio_clip"
    IMAGE = "image"
    TEXT = "text"
    SHAPE = "shape"


class SourceType(str, Enum):
    """Source type for track items."""

    VIDEO = "video"
    ASSET = "asset"
    TEXT = "text"
    GENERATED = "generated"


class TrackItem(SQLModel, table=True):
    """TrackItem model for elements on timeline tracks."""

    __tablename__ = "track_items"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    track_id: UUID = Field(foreign_key="tracks.id", index=True)
    item_type: ItemType = Field(default=ItemType.VIDEO_CLIP)
    source_type: SourceType = Field(default=SourceType.VIDEO)

    # Source reference
    source_id: UUID | None = Field(default=None)  # Reference to Video, Asset, etc.
    source_url: str | None = Field(default=None, max_length=500)

    # Timeline position
    start_time: float = Field(default=0.0, index=True)  # When item starts on timeline (seconds)
    end_time: float = Field(default=0.0)  # When item ends on timeline (seconds)
    duration: float = Field(default=0.0)  # Item duration (end_time - start_time)
    trim_start: float = Field(default=0.0)  # Trim from start of source (seconds)
    trim_end: float = Field(default=0.0)  # Trim from end of source (seconds)

    # Transform properties
    position_x: float = Field(default=0.0)  # 0.0 to 1.0 (0 = left, 0.5 = center, 1 = right)
    position_y: float = Field(default=0.0)  # 0.0 to 1.0 (0 = top, 0.5 = center, 1 = bottom)
    scale_x: float = Field(default=1.0)  # Horizontal scale
    scale_y: float = Field(default=1.0)  # Vertical scale
    rotation: float = Field(default=0.0)  # Rotation in degrees

    # Advanced settings stored as JSON
    crop_settings: dict | None = Field(default=None, sa_column=Column(JSON))
    transform_settings: dict | None = Field(default=None, sa_column=Column(JSON))
    text_content: str | None = Field(default=None)
    text_style: dict | None = Field(default=None, sa_column=Column(JSON))
    effects: list | None = Field(default=None, sa_column=Column(JSON))

    # Transitions
    transition_in_id: UUID | None = Field(default=None, foreign_key="transitions.id")
    transition_out_id: UUID | None = Field(default=None, foreign_key="transitions.id")

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    track: "Track" = Relationship(back_populates="items")
