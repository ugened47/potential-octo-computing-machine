"""Asset model for Advanced Editor."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import ARRAY, String
from sqlmodel import Column, Field, JSON, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.user import User


class AssetType(str, Enum):
    """Asset type."""

    IMAGE = "image"
    AUDIO = "audio"
    FONT = "font"
    GRAPHIC = "graphic"
    TEMPLATE = "template"


class Asset(SQLModel, table=True):
    """Asset model for reusable media assets."""

    __tablename__ = "assets"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    asset_type: AssetType = Field(default=AssetType.IMAGE, index=True)
    name: str = Field(max_length=255)

    # File metadata
    file_url: str = Field(max_length=500)  # S3 URL
    file_size: int | None = Field(default=None)  # bytes
    mime_type: str | None = Field(default=None, max_length=100)
    width: int | None = Field(default=None)  # For images
    height: int | None = Field(default=None)  # For images
    duration_seconds: float | None = Field(default=None)  # For audio

    # Additional metadata
    metadata: dict = Field(default_factory=dict, sa_column=Column(JSON))
    thumbnail_url: str | None = Field(default=None, max_length=500)
    is_public: bool = Field(default=False)
    tags: list[str] = Field(default_factory=list, sa_column=Column(ARRAY(String)))
    usage_count: int = Field(default=0)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
