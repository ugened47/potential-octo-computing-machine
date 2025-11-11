"""Notification model for in-app notifications."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.user import User


class NotificationType(str, Enum):
    """Types of notifications."""

    SHARE = "share"
    COMMENT = "comment"
    MENTION = "mention"
    VERSION = "version"
    ORGANIZATION = "organization"


class Notification(SQLModel, table=True):
    """Notification model for in-app notifications."""

    __tablename__ = "notifications"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)

    # Notification details
    type: NotificationType = Field(default=NotificationType.COMMENT)
    related_entity_type: str = Field(max_length=50)  # e.g., "video_share", "comment", "version"
    related_entity_id: UUID

    title: str = Field(max_length=255)
    message: str = Field(max_length=1000)

    # Read status
    is_read: bool = Field(default=False, index=True)
    read_at: datetime | None = Field(default=None)

    # Action
    action_url: str | None = Field(default=None, max_length=500)

    # Timestamp
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)

    # Relationships
    # user: Optional["User"] = Relationship()
