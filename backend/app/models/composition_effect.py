"""CompositionEffect model for Advanced Editor."""

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from sqlmodel import Column, Field, JSON, SQLModel


class EffectType(str, Enum):
    """Effect type."""

    FILTER = "filter"
    COLOR = "color"
    BLUR = "blur"
    SHARPEN = "sharpen"
    DISTORT = "distort"
    CUSTOM = "custom"


class CompositionEffect(SQLModel, table=True):
    """CompositionEffect model for reusable effects."""

    __tablename__ = "composition_effects"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(max_length=255)
    effect_type: EffectType = Field(default=EffectType.FILTER, index=True)

    # Effect parameters
    parameters: dict = Field(default_factory=dict, sa_column=Column(JSON))
    ffmpeg_filter: str | None = Field(default=None, max_length=500)
    is_builtin: bool = Field(default=True)
    preview_url: str | None = Field(default=None, max_length=500)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
