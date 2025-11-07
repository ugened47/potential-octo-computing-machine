"""Authentication API endpoints."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.auth import (
    AuthResponse,
    MessageResponse,
    TokenRefresh,
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
)
from app.services.auth import AuthService

router = APIRouter()


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Register a new user.

    Args:
        user_data: User registration data
        db: Database session

    Returns:
        AuthResponse: User and authentication tokens

    Raises:
        HTTPException: If email already exists
    """
    auth_service = AuthService(db)
    return await auth_service.register_user(
        email=user_data.email,
        password=user_data.password,
        full_name=user_data.full_name,
    )


@router.post("/login", response_model=AuthResponse)
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Authenticate user and return tokens.

    Args:
        credentials: User login credentials
        db: Database session

    Returns:
        AuthResponse: User and authentication tokens

    Raises:
        HTTPException: If credentials are invalid
    """
    auth_service = AuthService(db)
    return await auth_service.login_user(
        email=credentials.email,
        password=credentials.password,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    token_data: TokenRefresh,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Refresh access token using refresh token.

    Args:
        token_data: Refresh token data
        db: Database session

    Returns:
        TokenResponse: New access and refresh tokens

    Raises:
        HTTPException: If refresh token is invalid
    """
    auth_service = AuthService(db)
    return await auth_service.refresh_access_token(token_data.refresh_token)


@router.post("/logout", response_model=MessageResponse)
async def logout(
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Logout current user.

    Note: JWT tokens are stateless, so logout is handled client-side
    by removing the tokens from storage. This endpoint exists for
    consistency and can be extended for token blacklisting if needed.

    Args:
        current_user: Current authenticated user

    Returns:
        MessageResponse: Success message
    """
    return MessageResponse(message="Successfully logged out")


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get current user information.

    Args:
        current_user: Current authenticated user

    Returns:
        UserResponse: Current user data
    """
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    full_name: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Update current user information.

    Args:
        full_name: New full name
        current_user: Current authenticated user
        db: Database session

    Returns:
        UserResponse: Updated user data
    """
    current_user.full_name = full_name
    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)

    return UserResponse.model_validate(current_user)
