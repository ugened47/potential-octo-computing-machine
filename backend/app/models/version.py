"""Version model for video edit history and rollback."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel, Column, JSON

if TYPE_CHECKING:
    from app.models.video import Video
    from app.models.user import User


class ChangeType(str, Enum):
    """Types of changes that create new versions."""

    UPLOAD = "upload"
    EDIT = "edit"
    EXPORT = "export"
    SILENCE_REMOVAL = "silence_removal"
    CLIP = "clip"
    SUBTITLE = "subtitle"
    ROLLBACK = "rollback"


class Version(SQLModel, table=True):
    """Version model for video edit history and rollback."""

    __tablename__ = "versions"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    video_id: UUID = Field(foreign_key="videos.id", index=True)
    version_number: int = Field(index=True)  # Auto-increment per video, starts at 1
    created_by: UUID = Field(foreign_key="users.id")

    # Change information
    change_type: ChangeType = Field(default=ChangeType.EDIT)
    change_summary: str = Field(max_length=500)
    change_details: dict = Field(default_factory=dict, sa_column=Column(JSON))

    # Video state snapshot
    video_metadata_snapshot: dict = Field(default_factory=dict, sa_column=Column(JSON))
    file_url: str | None = Field(default=None, max_length=500)
    file_size: int | None = Field(default=None)  # In bytes
    duration: float | None = Field(default=None)  # In seconds

    # Additional snapshots
    transcript_snapshot: dict | None = Field(default=None, sa_column=Column(JSON))
    timeline_snapshot: dict | None = Field(default=None, sa_column=Column(JSON))

    # Version tracking
    parent_version_id: UUID | None = Field(default=None, foreign_key="versions.id")
    is_current: bool = Field(default=False, index=True)

    # Timestamp
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)

    # Relationships
    # video: Optional["Video"] = Relationship()
    # creator: Optional["User"] = Relationship()
    # parent_version: Optional["Version"] = Relationship()
