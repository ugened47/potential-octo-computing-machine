"""Transition model for Advanced Editor."""

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from sqlmodel import Column, Field, JSON, SQLModel


class TransitionType(str, Enum):
    """Transition type."""

    FADE = "fade"
    DISSOLVE = "dissolve"
    SLIDE = "slide"
    WIPE = "wipe"
    ZOOM = "zoom"
    BLUR = "blur"
    CUSTOM = "custom"


class TransitionDirection(str, Enum):
    """Transition direction."""

    IN = "in"
    OUT = "out"


class Transition(SQLModel, table=True):
    """Transition model for transition effects library."""

    __tablename__ = "transitions"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(max_length=255)
    transition_type: TransitionType = Field(default=TransitionType.FADE, index=True)
    direction: TransitionDirection | None = Field(default=None)
    default_duration: float = Field(default=0.5)  # Default transition length in seconds

    # Transition parameters
    parameters: dict = Field(default_factory=dict, sa_column=Column(JSON))
    preview_url: str | None = Field(default=None, max_length=500)
    is_builtin: bool = Field(default=True)
    is_public: bool = Field(default=True, index=True)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
