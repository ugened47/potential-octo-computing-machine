"""User model."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    """User model."""

    __tablename__ = "users"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(unique=True, index=True, max_length=255)
    hashed_password: str = Field(max_length=255)
    full_name: str | None = Field(default=None, max_length=255)
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # OAuth fields
    oauth_provider: str | None = Field(default=None, max_length=50)
    oauth_id: str | None = Field(default=None, max_length=255)

    # Email verification
    email_verified: bool = Field(default=False)
    email_verification_token: str | None = Field(default=None, max_length=255)
    email_verification_expires: datetime | None = Field(default=None)

    # Password reset
    password_reset_token: str | None = Field(default=None, max_length=255)
    password_reset_expires: datetime | None = Field(default=None)
