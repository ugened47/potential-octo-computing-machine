"""Tests for authentication service."""

import pytest
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.user import User
from app.services.auth import AuthService


@pytest.mark.asyncio
class TestAuthService:
    """Tests for AuthService."""

    async def test_register_user(self, db_session: AsyncSession):
        """Test user registration."""
        auth_service = AuthService(db_session)

        auth_response = await auth_service.register_user(
            email="test@example.com",
            password="SecurePass123!",
            full_name="Test User",
        )

        # Check response structure
        assert auth_response.access_token
        assert auth_response.refresh_token
        assert auth_response.token_type == "bearer"
        assert auth_response.user.email == "test@example.com"
        assert auth_response.user.full_name == "Test User"
        assert auth_response.user.is_active is True

        # Verify user in database
        result = await db_session.execute(
            select(User).where(User.email == "test@example.com")
        )
        user = result.scalar_one_or_none()
        assert user is not None
        assert user.email == "test@example.com"
        assert user.hashed_password != "SecurePass123!"  # Password should be hashed

    async def test_register_user_duplicate_email(self, db_session: AsyncSession):
        """Test that registering duplicate email fails."""
        auth_service = AuthService(db_session)

        # Register first user
        await auth_service.register_user(
            email="duplicate@example.com",
            password="SecurePass123!",
        )

        # Try to register again with same email
        with pytest.raises(Exception) as exc_info:
            await auth_service.register_user(
                email="duplicate@example.com",
                password="DifferentPass123!",
            )

        assert exc_info.value.status_code == 400
        assert "already registered" in str(exc_info.value.detail).lower()

    async def test_login_user_success(self, db_session: AsyncSession):
        """Test successful user login."""
        auth_service = AuthService(db_session)

        # Register user
        await auth_service.register_user(
            email="login@example.com",
            password="SecurePass123!",
            full_name="Login User",
        )

        # Login
        auth_response = await auth_service.login_user(
            email="login@example.com",
            password="SecurePass123!",
        )

        assert auth_response.access_token
        assert auth_response.refresh_token
        assert auth_response.user.email == "login@example.com"
        assert auth_response.user.full_name == "Login User"

    async def test_login_user_wrong_password(self, db_session: AsyncSession):
        """Test login with wrong password."""
        auth_service = AuthService(db_session)

        # Register user
        await auth_service.register_user(
            email="wrongpass@example.com",
            password="CorrectPass123!",
        )

        # Try to login with wrong password
        with pytest.raises(Exception) as exc_info:
            await auth_service.login_user(
                email="wrongpass@example.com",
                password="WrongPass123!",
            )

        assert exc_info.value.status_code == 401

    async def test_login_user_not_found(self, db_session: AsyncSession):
        """Test login with non-existent user."""
        auth_service = AuthService(db_session)

        with pytest.raises(Exception) as exc_info:
            await auth_service.login_user(
                email="notfound@example.com",
                password="SecurePass123!",
            )

        assert exc_info.value.status_code == 401

    async def test_login_inactive_user(self, db_session: AsyncSession):
        """Test that inactive user cannot login."""
        auth_service = AuthService(db_session)

        # Register user
        await auth_service.register_user(
            email="inactive@example.com",
            password="SecurePass123!",
        )

        # Set user as inactive
        result = await db_session.execute(
            select(User).where(User.email == "inactive@example.com")
        )
        user = result.scalar_one()
        user.is_active = False
        db_session.add(user)
        await db_session.commit()

        # Try to login
        with pytest.raises(Exception) as exc_info:
            await auth_service.login_user(
                email="inactive@example.com",
                password="SecurePass123!",
            )

        assert exc_info.value.status_code == 403
        assert "inactive" in str(exc_info.value.detail).lower()

    async def test_refresh_access_token(self, db_session: AsyncSession):
        """Test token refresh."""
        auth_service = AuthService(db_session)

        # Register user
        auth_response = await auth_service.register_user(
            email="refresh@example.com",
            password="SecurePass123!",
        )

        # Refresh token
        token_response = await auth_service.refresh_access_token(
            auth_response.refresh_token
        )

        assert token_response.access_token
        assert token_response.refresh_token
        assert token_response.token_type == "bearer"

        # New tokens should be different from original
        assert token_response.access_token != auth_response.access_token
        assert token_response.refresh_token != auth_response.refresh_token

    async def test_refresh_with_invalid_token(self, db_session: AsyncSession):
        """Test refresh with invalid token."""
        auth_service = AuthService(db_session)

        with pytest.raises(Exception) as exc_info:
            await auth_service.refresh_access_token("invalid.token.here")

        assert exc_info.value.status_code == 401

    async def test_refresh_with_access_token(self, db_session: AsyncSession):
        """Test that refresh fails when using access token instead of refresh token."""
        auth_service = AuthService(db_session)

        # Register user
        auth_response = await auth_service.register_user(
            email="wrongtype@example.com",
            password="SecurePass123!",
        )

        # Try to refresh with access token
        with pytest.raises(Exception) as exc_info:
            await auth_service.refresh_access_token(auth_response.access_token)

        assert exc_info.value.status_code == 401
        assert "invalid token type" in str(exc_info.value.detail).lower()

    async def test_refresh_token_inactive_user(self, db_session: AsyncSession):
        """Test that refresh fails for inactive user."""
        auth_service = AuthService(db_session)

        # Register user
        auth_response = await auth_service.register_user(
            email="refreshinactive@example.com",
            password="SecurePass123!",
        )

        # Set user as inactive
        result = await db_session.execute(
            select(User).where(User.email == "refreshinactive@example.com")
        )
        user = result.scalar_one()
        user.is_active = False
        db_session.add(user)
        await db_session.commit()

        # Try to refresh token
        with pytest.raises(Exception) as exc_info:
            await auth_service.refresh_access_token(auth_response.refresh_token)

        assert exc_info.value.status_code == 403

    async def test_get_user_by_id(self, db_session: AsyncSession):
        """Test getting user by ID."""
        auth_service = AuthService(db_session)

        # Register user
        auth_response = await auth_service.register_user(
            email="getbyid@example.com",
            password="SecurePass123!",
        )

        user_id = auth_response.user.id

        # Get user by ID
        user = await auth_service.get_user_by_id(user_id)

        assert user is not None
        assert user.id == user_id
        assert user.email == "getbyid@example.com"

    async def test_get_user_by_id_not_found(self, db_session: AsyncSession):
        """Test getting user by non-existent ID."""
        auth_service = AuthService(db_session)

        user = await auth_service.get_user_by_id(uuid4())
        assert user is None

    async def test_get_user_by_email(self, db_session: AsyncSession):
        """Test getting user by email."""
        auth_service = AuthService(db_session)

        # Register user
        await auth_service.register_user(
            email="getbyemail@example.com",
            password="SecurePass123!",
        )

        # Get user by email
        user = await auth_service.get_user_by_email("getbyemail@example.com")

        assert user is not None
        assert user.email == "getbyemail@example.com"

    async def test_get_user_by_email_not_found(self, db_session: AsyncSession):
        """Test getting user by non-existent email."""
        auth_service = AuthService(db_session)

        user = await auth_service.get_user_by_email("notfound@example.com")
        assert user is None

    async def test_register_user_without_full_name(self, db_session: AsyncSession):
        """Test registering user without full name."""
        auth_service = AuthService(db_session)

        auth_response = await auth_service.register_user(
            email="noname@example.com",
            password="SecurePass123!",
        )

        assert auth_response.user.full_name is None

        # Verify in database
        result = await db_session.execute(
            select(User).where(User.email == "noname@example.com")
        )
        user = result.scalar_one()
        assert user.full_name is None

    async def test_user_defaults(self, db_session: AsyncSession):
        """Test that user defaults are set correctly."""
        auth_service = AuthService(db_session)

        auth_response = await auth_service.register_user(
            email="defaults@example.com",
            password="SecurePass123!",
        )

        user_id = auth_response.user.id
        result = await db_session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one()

        # Check defaults
        assert user.is_active is True
        assert user.is_superuser is False
        assert user.oauth_provider is None
        assert user.oauth_id is None
        assert user.created_at is not None
        assert user.updated_at is not None
