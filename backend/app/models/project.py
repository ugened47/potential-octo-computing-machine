"""Project model for Advanced Editor."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlmodel import Column, Field, JSON, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.track import Track
    from app.models.user import User
    from app.models.video import Video


class ProjectStatus(str, Enum):
    """Project status."""

    DRAFT = "draft"
    RENDERING = "rendering"
    COMPLETED = "completed"
    ERROR = "error"


class Project(SQLModel, table=True):
    """Project model for multi-track compositions."""

    __tablename__ = "projects"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    name: str = Field(max_length=255)
    description: str | None = Field(default=None)
    video_id: UUID | None = Field(default=None, foreign_key="videos.id")

    # Output settings
    width: int = Field(default=1920)  # Output width in pixels
    height: int = Field(default=1080)  # Output height in pixels
    frame_rate: float = Field(default=30.0)  # Output frame rate
    duration_seconds: float = Field(default=0.0)  # Total project duration
    background_color: str = Field(default="#000000", max_length=7)  # Hex color

    # Settings stored as JSON
    canvas_settings: dict = Field(default_factory=dict, sa_column=Column(JSON))
    export_settings: dict = Field(default_factory=dict, sa_column=Column(JSON))

    # Render output
    thumbnail_url: str | None = Field(default=None, max_length=500)
    status: ProjectStatus = Field(default=ProjectStatus.DRAFT)
    last_rendered_at: datetime | None = Field(default=None)
    render_output_url: str | None = Field(default=None, max_length=500)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    tracks: list["Track"] = Relationship(back_populates="project", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
