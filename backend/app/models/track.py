"""Track model for Advanced Editor."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.track_item import TrackItem


class TrackType(str, Enum):
    """Track type."""

    VIDEO = "video"
    AUDIO = "audio"
    IMAGE = "image"
    TEXT = "text"
    OVERLAY = "overlay"


class BlendMode(str, Enum):
    """Blend mode for compositing."""

    NORMAL = "normal"
    MULTIPLY = "multiply"
    SCREEN = "screen"
    OVERLAY = "overlay"


class Track(SQLModel, table=True):
    """Track model for timeline tracks."""

    __tablename__ = "tracks"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    project_id: UUID = Field(foreign_key="projects.id", index=True)
    track_type: TrackType = Field(default=TrackType.VIDEO)
    name: str = Field(max_length=255)

    # Visual/audio properties
    z_index: int = Field(default=0, index=True)  # Stacking order (higher = on top)
    is_locked: bool = Field(default=False)
    is_visible: bool = Field(default=True)
    is_muted: bool = Field(default=False)
    volume: float = Field(default=1.0)  # 0.0 to 1.0
    opacity: float = Field(default=1.0)  # 0.0 to 1.0
    blend_mode: BlendMode = Field(default=BlendMode.NORMAL)
    track_order: int = Field(default=0, index=True)  # Order in UI (0 = top)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    project: "Project" = Relationship(back_populates="tracks")
    items: list["TrackItem"] = Relationship(back_populates="track", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
