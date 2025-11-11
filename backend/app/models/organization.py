"""Organization model for team collaboration."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel, Column, JSON

if TYPE_CHECKING:
    from app.models.team_member import TeamMember
    from app.models.video_permission import VideoPermission
    from app.models.user import User


class OrganizationPlan(str, Enum):
    """Organization plan types."""

    FREE = "free"
    PRO = "pro"
    BUSINESS = "business"


class Organization(SQLModel, table=True):
    """Organization model for team collaboration."""

    __tablename__ = "organizations"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(min_length=2, max_length=100)
    slug: str = Field(unique=True, index=True, max_length=100)
    owner_id: UUID = Field(foreign_key="users.id", index=True)
    plan: OrganizationPlan = Field(default=OrganizationPlan.FREE)
    max_members: int = Field(default=1)
    settings: dict = Field(default_factory=dict, sa_column=Column(JSON))

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    # owner: "User" = Relationship()
    # members: list["TeamMember"] = Relationship(back_populates="organization")
    # permissions: list["VideoPermission"] = Relationship(back_populates="organization")
