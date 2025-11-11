"""API dependencies for dependency injection."""

from collections.abc import AsyncGenerator
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

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
    user_id_str: str | None = payload.get("sub")
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


# Team Collaboration Dependencies


async def get_permission_service(
    db: AsyncSession = Depends(get_db),
):
    """Get permission service instance.

    Args:
        db: Database session

    Returns:
        PermissionService instance
    """
    from app.services.permission import PermissionService

    return PermissionService(db)


async def get_sharing_service(
    db: AsyncSession = Depends(get_db),
):
    """Get sharing service instance.

    Args:
        db: Database session

    Returns:
        SharingService instance
    """
    from app.services.sharing import SharingService

    return SharingService(db)


async def get_notification_service(
    db: AsyncSession = Depends(get_db),
):
    """Get notification service instance.

    Args:
        db: Database session

    Returns:
        NotificationService instance
    """
    from app.services.notification import NotificationService

    return NotificationService(db)


async def get_version_service(
    db: AsyncSession = Depends(get_db),
):
    """Get version service instance.

    Args:
        db: Database session

    Returns:
        VersionService instance
    """
    from app.services.version import VersionService

    return VersionService(db)


async def get_comment_service(
    db: AsyncSession = Depends(get_db),
):
    """Get comment service instance.

    Args:
        db: Database session

    Returns:
        CommentService instance
    """
    from app.services.comment import CommentService

    return CommentService(db)


async def require_video_view_permission(
    video_id: UUID,
    current_user: User = Depends(get_current_user),
    permission_service = Depends(get_permission_service),
) -> User:
    """Require user to have view permission for video.

    Args:
        video_id: Video ID
        current_user: Current authenticated user
        permission_service: Permission service

    Returns:
        Current user if authorized

    Raises:
        AuthorizationError: If user doesn't have permission
    """
    result = await permission_service.can_view_video(current_user.id, video_id)
    if not result.allowed:
        raise AuthorizationError(f"Cannot view video: {result.reason}")
    return current_user


async def require_video_edit_permission(
    video_id: UUID,
    current_user: User = Depends(get_current_user),
    permission_service = Depends(get_permission_service),
) -> User:
    """Require user to have edit permission for video.

    Args:
        video_id: Video ID
        current_user: Current authenticated user
        permission_service: Permission service

    Returns:
        Current user if authorized

    Raises:
        AuthorizationError: If user doesn't have permission
    """
    result = await permission_service.can_edit_video(current_user.id, video_id)
    if not result.allowed:
        raise AuthorizationError(f"Cannot edit video: {result.reason}")
    return current_user


async def require_video_delete_permission(
    video_id: UUID,
    current_user: User = Depends(get_current_user),
    permission_service = Depends(get_permission_service),
) -> User:
    """Require user to have delete permission for video.

    Args:
        video_id: Video ID
        current_user: Current authenticated user
        permission_service: Permission service

    Returns:
        Current user if authorized

    Raises:
        AuthorizationError: If user doesn't have permission
    """
    result = await permission_service.can_delete_video(current_user.id, video_id)
    if not result.allowed:
        raise AuthorizationError(f"Cannot delete video: {result.reason}")
    return current_user


async def require_organization_admin(
    organization_id: UUID,
    current_user: User = Depends(get_current_user),
    permission_service = Depends(get_permission_service),
) -> User:
    """Require user to be organization admin.

    Args:
        organization_id: Organization ID
        current_user: Current authenticated user
        permission_service: Permission service

    Returns:
        Current user if authorized

    Raises:
        AuthorizationError: If user is not admin
    """
    result = await permission_service.can_manage_organization(
        current_user.id, organization_id
    )
    if not result.allowed:
        raise AuthorizationError(f"Not an organization admin: {result.reason}")
    return current_user
