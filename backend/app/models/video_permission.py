"""VideoPermission model for granular video access control."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.video import Video
    from app.models.organization import Organization
    from app.models.user import User


class PermissionLevel(str, Enum):
    """Permission levels for video access."""

    VIEW = "view"
    COMMENT = "comment"
    EDIT = "edit"
    ADMIN = "admin"


class VideoPermission(SQLModel, table=True):
    """VideoPermission model for granular video access control."""

    __tablename__ = "video_permissions"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    video_id: UUID = Field(foreign_key="videos.id", index=True)

    # Either organization_id or user_id must be set (not both)
    organization_id: UUID | None = Field(default=None, foreign_key="organizations.id", index=True)
    user_id: UUID | None = Field(default=None, foreign_key="users.id", index=True)

    permission_level: PermissionLevel = Field(default=PermissionLevel.VIEW, index=True)
    granted_by: UUID = Field(foreign_key="users.id")
    granted_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime | None = Field(default=None)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    # video: Optional["Video"] = Relationship()
    # organization: Optional["Organization"] = Relationship(back_populates="permissions")
    # user: Optional["User"] = Relationship()
