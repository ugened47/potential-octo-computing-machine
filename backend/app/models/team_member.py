"""TeamMember model for organization membership."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.user import User


class MemberRole(str, Enum):
    """Team member roles."""

    VIEWER = "viewer"
    EDITOR = "editor"
    ADMIN = "admin"


class MemberStatus(str, Enum):
    """Team member status."""

    INVITED = "invited"
    ACTIVE = "active"
    SUSPENDED = "suspended"


class TeamMember(SQLModel, table=True):
    """TeamMember model for organization membership."""

    __tablename__ = "team_members"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    organization_id: UUID = Field(foreign_key="organizations.id", index=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    role: MemberRole = Field(default=MemberRole.VIEWER, index=True)
    status: MemberStatus = Field(default=MemberStatus.INVITED, index=True)

    # Invitation tracking
    invited_by: UUID | None = Field(default=None, foreign_key="users.id")
    invited_at: datetime | None = Field(default=None)
    joined_at: datetime | None = Field(default=None)
    last_active_at: datetime | None = Field(default=None)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    # organization: Optional["Organization"] = Relationship(back_populates="members")
    # user: Optional["User"] = Relationship()
