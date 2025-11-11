"""CommentReaction model for emoji reactions on comments."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.comment import Comment
    from app.models.user import User


class ReactionType(str, Enum):
    """Reaction types for comments."""

    LIKE = "like"
    LOVE = "love"
    LAUGH = "laugh"
    CONFUSED = "confused"
    EYES = "eyes"


class CommentReaction(SQLModel, table=True):
    """CommentReaction model for emoji reactions on comments."""

    __tablename__ = "comment_reactions"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    comment_id: UUID = Field(foreign_key="comments.id", index=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    reaction_type: ReactionType = Field(default=ReactionType.LIKE)

    # Timestamp
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    # comment: Optional["Comment"] = Relationship(back_populates="reactions")
    # user: Optional["User"] = Relationship()
