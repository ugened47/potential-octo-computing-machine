"""Unit tests for authentication service."""

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from app.models.user import User
from app.services.auth import AuthService
from app.core.security import verify_password, decode_token


@pytest.mark.asyncio
async def test_register_user_success(db_session: AsyncSession):
    """Test successful user registration."""
    service = AuthService(db_session)

    auth_response = await service.register_user(
        email="test@example.com",
        password="Test123!",
        full_name="Test User"
    )

    # Verify user response
    assert auth_response.user.email == "test@example.com"
    assert auth_response.user.full_name == "Test User"
    assert auth_response.user.id is not None
    assert auth_response.user.is_active is True

    # Verify tokens are generated
    assert auth_response.access_token is not None
    assert auth_response.refresh_token is not None

    # Verify password is hashed
    assert auth_response.user.email == "test@example.com"


@pytest.mark.asyncio
async def test_register_user_duplicate_email(db_session: AsyncSession):
    """Test registration with duplicate email fails."""
    service = AuthService(db_session)

    # Register first user
    await service.register_user(
        email="test@example.com",
        password="Test123!"
    )

    # Try to register with same email
    with pytest.raises(HTTPException) as exc_info:
        await service.register_user(
            email="test@example.com",
            password="AnotherPassword123!"
        )

    assert exc_info.value.status_code == 400
    assert "already registered" in str(exc_info.value.detail).lower()


@pytest.mark.asyncio
async def test_register_user_without_full_name(db_session: AsyncSession):
    """Test registration without full name."""
    service = AuthService(db_session)

    auth_response = await service.register_user(
        email="test@example.com",
        password="Test123!"
    )

    assert auth_response.user.email == "test@example.com"
    assert auth_response.user.full_name is None


@pytest.mark.asyncio
async def test_login_user_success(db_session: AsyncSession):
    """Test successful user login."""
    service = AuthService(db_session)

    # Register user first
    await service.register_user(
        email="test@example.com",
        password="Test123!",
        full_name="Test User"
    )

    # Login
    auth_response = await service.login_user(
        email="test@example.com",
        password="Test123!"
    )

    assert auth_response.user.email == "test@example.com"
    assert auth_response.user.full_name == "Test User"
    assert auth_response.access_token is not None
    assert auth_response.refresh_token is not None


@pytest.mark.asyncio
async def test_login_user_wrong_password(db_session: AsyncSession):
    """Test login with incorrect password fails."""
    service = AuthService(db_session)

    # Register user
    await service.register_user(
        email="test@example.com",
        password="Test123!"
    )

    # Try to login with wrong password
    with pytest.raises(HTTPException) as exc_info:
        await service.login_user(
            email="test@example.com",
            password="WrongPassword!"
        )

    assert exc_info.value.status_code == 401
    assert "incorrect" in str(exc_info.value.detail).lower()


@pytest.mark.asyncio
async def test_login_user_not_found(db_session: AsyncSession):
    """Test login with non-existent user fails."""
    service = AuthService(db_session)

    with pytest.raises(HTTPException) as exc_info:
        await service.login_user(
            email="nonexistent@example.com",
            password="Test123!"
        )

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_login_inactive_user(db_session: AsyncSession):
    """Test login with inactive user account fails."""
    service = AuthService(db_session)

    # Create inactive user directly
    user = User(
        email="inactive@example.com",
        hashed_password="hashed_password",
        is_active=False
    )
    db_session.add(user)
    await db_session.commit()

    # Try to login
    with pytest.raises(HTTPException) as exc_info:
        await service.login_user(
            email="inactive@example.com",
            password="Test123!"
        )

    assert exc_info.value.status_code == 403
    assert "inactive" in str(exc_info.value.detail).lower()


@pytest.mark.asyncio
async def test_refresh_access_token_success(db_session: AsyncSession):
    """Test successful token refresh."""
    service = AuthService(db_session)

    # Register user
    auth_response = await service.register_user(
        email="test@example.com",
        password="Test123!"
    )

    # Refresh token
    token_response = await service.refresh_access_token(
        auth_response.refresh_token
    )

    assert token_response.access_token is not None
    assert token_response.refresh_token is not None
    assert token_response.access_token != auth_response.access_token


@pytest.mark.asyncio
async def test_refresh_access_token_invalid_token(db_session: AsyncSession):
    """Test token refresh with invalid token fails."""
    service = AuthService(db_session)

    with pytest.raises(HTTPException) as exc_info:
        await service.refresh_access_token("invalid_token")

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_refresh_access_token_wrong_type(db_session: AsyncSession):
    """Test token refresh with access token (wrong type) fails."""
    from app.core.security import create_access_token

    service = AuthService(db_session)

    # Create user
    user = User(email="test@example.com", hashed_password="hashed")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Try to use access token for refresh
    access_token = create_access_token(data={"sub": str(user.id)})

    with pytest.raises(HTTPException) as exc_info:
        await service.refresh_access_token(access_token)

    assert exc_info.value.status_code == 401
    assert "token type" in str(exc_info.value.detail).lower()


@pytest.mark.asyncio
async def test_refresh_token_user_not_found(db_session: AsyncSession):
    """Test token refresh when user no longer exists."""
    from app.core.security import create_refresh_token

    service = AuthService(db_session)

    # Create token for non-existent user
    fake_user_id = uuid4()
    refresh_token = create_refresh_token(data={"sub": str(fake_user_id)})

    with pytest.raises(HTTPException) as exc_info:
        await service.refresh_access_token(refresh_token)

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_refresh_token_inactive_user(db_session: AsyncSession):
    """Test token refresh with inactive user fails."""
    from app.core.security import create_refresh_token

    service = AuthService(db_session)

    # Create inactive user
    user = User(
        email="inactive@example.com",
        hashed_password="hashed",
        is_active=False
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Create refresh token
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    with pytest.raises(HTTPException) as exc_info:
        await service.refresh_access_token(refresh_token)

    assert exc_info.value.status_code == 403
    assert "inactive" in str(exc_info.value.detail).lower()


@pytest.mark.asyncio
async def test_get_user_by_id_success(db_session: AsyncSession):
    """Test getting user by ID."""
    service = AuthService(db_session)

    # Create user
    user = User(email="test@example.com", hashed_password="hashed")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Get user by ID
    found_user = await service.get_user_by_id(user.id)

    assert found_user is not None
    assert found_user.id == user.id
    assert found_user.email == "test@example.com"


@pytest.mark.asyncio
async def test_get_user_by_id_not_found(db_session: AsyncSession):
    """Test getting user by non-existent ID."""
    service = AuthService(db_session)

    fake_id = uuid4()
    found_user = await service.get_user_by_id(fake_id)

    assert found_user is None


@pytest.mark.asyncio
async def test_get_user_by_email_success(db_session: AsyncSession):
    """Test getting user by email."""
    service = AuthService(db_session)

    # Create user
    user = User(email="test@example.com", hashed_password="hashed")
    db_session.add(user)
    await db_session.commit()

    # Get user by email
    found_user = await service.get_user_by_email("test@example.com")

    assert found_user is not None
    assert found_user.email == "test@example.com"


@pytest.mark.asyncio
async def test_get_user_by_email_not_found(db_session: AsyncSession):
    """Test getting user by non-existent email."""
    service = AuthService(db_session)

    found_user = await service.get_user_by_email("nonexistent@example.com")

    assert found_user is None


@pytest.mark.asyncio
async def test_password_is_hashed(db_session: AsyncSession):
    """Test that password is properly hashed during registration."""
    service = AuthService(db_session)

    password = "Test123!"
    auth_response = await service.register_user(
        email="test@example.com",
        password=password
    )

    # Get user from database
    user = await service.get_user_by_email("test@example.com")
    assert user is not None

    # Verify password is hashed (not stored in plain text)
    assert user.hashed_password != password

    # Verify password can be verified
    assert verify_password(password, user.hashed_password)


@pytest.mark.asyncio
async def test_tokens_are_valid_jwt(db_session: AsyncSession):
    """Test that generated tokens are valid JWTs."""
    service = AuthService(db_session)

    auth_response = await service.register_user(
        email="test@example.com",
        password="Test123!"
    )

    # Decode access token
    access_payload = decode_token(auth_response.access_token)
    assert access_payload is not None
    assert access_payload.get("sub") == str(auth_response.user.id)
    assert access_payload.get("type") == "access"

    # Decode refresh token
    refresh_payload = decode_token(auth_response.refresh_token)
    assert refresh_payload is not None
    assert refresh_payload.get("sub") == str(auth_response.user.id)
    assert refresh_payload.get("type") == "refresh"
