"""VideoShare model for sharing videos with users and teams."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.video import Video
    from app.models.organization import Organization
    from app.models.user import User


class SharePermissionLevel(str, Enum):
    """Permission levels for shared videos."""

    VIEW = "view"
    COMMENT = "comment"
    EDIT = "edit"


class ShareAccessType(str, Enum):
    """Access types for video shares."""

    DIRECT = "direct"  # Shared with specific user
    LINK = "link"  # Anyone with link
    ORGANIZATION = "organization"  # Shared with entire organization


class VideoShare(SQLModel, table=True):
    """VideoShare model for sharing videos with users and teams."""

    __tablename__ = "video_shares"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    video_id: UUID = Field(foreign_key="videos.id", index=True)
    shared_by: UUID = Field(foreign_key="users.id", index=True)

    # Either shared_with_user_id or shared_with_organization_id must be set
    shared_with_user_id: UUID | None = Field(default=None, foreign_key="users.id", index=True)
    shared_with_organization_id: UUID | None = Field(
        default=None, foreign_key="organizations.id", index=True
    )

    permission_level: SharePermissionLevel = Field(default=SharePermissionLevel.VIEW)
    access_type: ShareAccessType = Field(default=ShareAccessType.DIRECT)

    # Link sharing
    share_token: str = Field(unique=True, index=True, max_length=64)
    expires_at: datetime | None = Field(default=None, index=True)
    is_active: bool = Field(default=True)

    # Access tracking
    access_count: int = Field(default=0)
    last_accessed_at: datetime | None = Field(default=None)

    # Optional message
    message: str | None = Field(default=None)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    # video: Optional["Video"] = Relationship()
    # sharer: Optional["User"] = Relationship()
    # shared_with_user: Optional["User"] = Relationship()
    # shared_with_organization: Optional["Organization"] = Relationship()
