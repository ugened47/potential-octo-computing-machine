"""Comment model for timeline comments and discussions."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel, Column, JSON
from sqlalchemy import ARRAY
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

if TYPE_CHECKING:
    from app.models.video import Video
    from app.models.user import User
    from app.models.comment_reaction import CommentReaction


class Comment(SQLModel, table=True):
    """Comment model for timeline comments and discussions."""

    __tablename__ = "comments"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    video_id: UUID = Field(foreign_key="videos.id", index=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)

    # For nested replies
    parent_comment_id: UUID | None = Field(default=None, foreign_key="comments.id", index=True)

    # Timeline position
    timestamp: float = Field(index=True)  # Video timestamp in seconds
    timestamp_end: float | None = Field(default=None)  # For range comments

    # Content
    content: str = Field(min_length=1, max_length=10000)
    mentions: list[UUID] = Field(default_factory=list, sa_column=Column(ARRAY(PG_UUID(as_uuid=True))))
    attachments: list = Field(default_factory=list, sa_column=Column(JSON))

    # Resolution tracking
    is_resolved: bool = Field(default=False, index=True)
    resolved_by: UUID | None = Field(default=None, foreign_key="users.id")
    resolved_at: datetime | None = Field(default=None)

    # Edit tracking
    is_edited: bool = Field(default=False)
    edited_at: datetime | None = Field(default=None)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    # video: Optional["Video"] = Relationship()
    # user: Optional["User"] = Relationship()
    # parent_comment: Optional["Comment"] = Relationship()
    # replies: list["Comment"] = Relationship(back_populates="parent_comment")
    # reactions: list["CommentReaction"] = Relationship(back_populates="comment")
