"""API dependencies for dependency injection."""

from typing import AsyncGenerator, Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.config import settings
from app.core.db import async_session_maker
from app.core.exceptions import AuthenticationError, AuthorizationError, NotFoundError
from app.core.security import decode_token
from app.models.user import User

# HTTP Bearer token scheme
security = HTTPBearer()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session.

    Yields:
        AsyncSession: Database session
    """
    async with async_session_maker() as session:
        yield session


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Get current authenticated user from JWT token.

    Args:
        credentials: HTTP Bearer token
        db: Database session

    Returns:
        User: Current authenticated user

    Raises:
        HTTPException: If token is invalid or user not found
    """
    token = credentials.credentials

    # Decode token
    payload = decode_token(token)
    if not payload:
        raise AuthenticationError("Could not validate credentials")

    # Verify token type
    token_type = payload.get("type")
    if token_type != "access":
        raise AuthenticationError("Invalid token type")

    # Get user ID from token
    user_id_str: Optional[str] = payload.get("sub")
    if not user_id_str:
        raise AuthenticationError("Token missing user ID")

    try:
        user_id = UUID(user_id_str)
    except ValueError:
        raise AuthenticationError("Invalid user ID in token")

    # Get user from database
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise NotFoundError("User", str(user_id))

    if not user.is_active:
        raise AuthorizationError("Inactive user")

    return user


async def get_current_active_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get current superuser (admin).

    Args:
        current_user: Current authenticated user

    Returns:
        User: Current superuser

    Raises:
        HTTPException: If user is not a superuser
    """
    if not current_user.is_superuser:
        raise AuthorizationError("Not enough permissions")
    return current_user
