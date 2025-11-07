"""Authentication schemas for request/response validation."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, validator


# Request schemas
class UserRegister(BaseModel):
    """User registration request."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=100)
    full_name: Optional[str] = Field(None, max_length=255)

    @validator("password")
    def password_strength(cls, v: str) -> str:
        """Validate password strength."""
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserLogin(BaseModel):
    """User login request."""

    email: EmailStr
    password: str


class TokenRefresh(BaseModel):
    """Token refresh request."""

    refresh_token: str


class PasswordResetRequest(BaseModel):
    """Password reset request (forgot password)."""

    email: EmailStr


class PasswordReset(BaseModel):
    """Password reset with token."""

    token: str
    new_password: str = Field(min_length=8, max_length=100)

    @validator("new_password")
    def password_strength(cls, v: str) -> str:
        """Validate password strength."""
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


# Response schemas
class TokenResponse(BaseModel):
    """JWT token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """User response (public fields only)."""

    id: UUID
    email: EmailStr
    full_name: Optional[str]
    is_active: bool
    created_at: datetime
    oauth_provider: Optional[str] = None

    class Config:
        """Pydantic config."""

        from_attributes = True


class AuthResponse(BaseModel):
    """Authentication response with user and tokens."""

    user: UserResponse
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class MessageResponse(BaseModel):
    """Generic message response."""

    message: str
