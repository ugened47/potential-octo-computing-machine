"""Tests for authentication API endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.user import User
from app.core.security import create_access_token, create_refresh_token, verify_password


class TestUserRegistration:
    """Tests for user registration endpoint."""

    def test_register_new_user(self, client: TestClient):
        """Test successful user registration."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "SecurePass123!",
                "full_name": "New User",
            },
        )

        assert response.status_code == 201
        data = response.json()

        # Check response structure
        assert "user" in data
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

        # Check user data
        user = data["user"]
        assert user["email"] == "newuser@example.com"
        assert user["full_name"] == "New User"
        assert user["is_active"] is True
        assert "id" in user
        assert "created_at" in user

    def test_register_duplicate_email(self, client: TestClient):
        """Test registration with duplicate email fails."""
        # Register first user
        client.post(
            "/api/auth/register",
            json={
                "email": "duplicate@example.com",
                "password": "SecurePass123!",
            },
        )

        # Try to register again with same email
        response = client.post(
            "/api/auth/register",
            json={
                "email": "duplicate@example.com",
                "password": "DifferentPass123!",
            },
        )

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    def test_register_invalid_email(self, client: TestClient):
        """Test registration with invalid email format."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "not-an-email",
                "password": "SecurePass123!",
            },
        )

        assert response.status_code == 422
        error = response.json()
        assert error["error"]["code"] == "VALIDATION_ERROR"

    def test_register_weak_password_no_uppercase(self, client: TestClient):
        """Test registration with weak password (no uppercase)."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com",
                "password": "weakpass123",
            },
        )

        assert response.status_code == 422
        error = response.json()
        assert "uppercase" in str(error).lower()

    def test_register_weak_password_no_lowercase(self, client: TestClient):
        """Test registration with weak password (no lowercase)."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com",
                "password": "WEAKPASS123",
            },
        )

        assert response.status_code == 422
        error = response.json()
        assert "lowercase" in str(error).lower()

    def test_register_weak_password_no_digit(self, client: TestClient):
        """Test registration with weak password (no digit)."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com",
                "password": "WeakPassword",
            },
        )

        assert response.status_code == 422
        error = response.json()
        assert "digit" in str(error).lower()

    def test_register_password_too_short(self, client: TestClient):
        """Test registration with password too short."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com",
                "password": "Pass1",  # Less than 8 characters
            },
        )

        assert response.status_code == 422

    def test_register_without_full_name(self, client: TestClient):
        """Test registration without full name (optional field)."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "noname@example.com",
                "password": "SecurePass123!",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["user"]["full_name"] is None


class TestUserLogin:
    """Tests for user login endpoint."""

    def test_login_success(self, client: TestClient):
        """Test successful login."""
        # Register user first
        client.post(
            "/api/auth/register",
            json={
                "email": "logintest@example.com",
                "password": "SecurePass123!",
                "full_name": "Login Test",
            },
        )

        # Login
        response = client.post(
            "/api/auth/login",
            json={
                "email": "logintest@example.com",
                "password": "SecurePass123!",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert "user" in data
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "logintest@example.com"

    def test_login_wrong_password(self, client: TestClient):
        """Test login with wrong password."""
        # Register user
        client.post(
            "/api/auth/register",
            json={
                "email": "wrongpass@example.com",
                "password": "CorrectPass123!",
            },
        )

        # Try to login with wrong password
        response = client.post(
            "/api/auth/login",
            json={
                "email": "wrongpass@example.com",
                "password": "WrongPass123!",
            },
        )

        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    def test_login_nonexistent_user(self, client: TestClient):
        """Test login with non-existent email."""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "notexist@example.com",
                "password": "SecurePass123!",
            },
        )

        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    def test_login_invalid_email_format(self, client: TestClient):
        """Test login with invalid email format."""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "not-an-email",
                "password": "SecurePass123!",
            },
        )

        assert response.status_code == 422


class TestTokenRefresh:
    """Tests for token refresh endpoint."""

    def test_refresh_token_success(self, client: TestClient):
        """Test successful token refresh."""
        # Register and get tokens
        register_response = client.post(
            "/api/auth/register",
            json={
                "email": "refresh@example.com",
                "password": "SecurePass123!",
            },
        )

        refresh_token = register_response.json()["refresh_token"]

        # Refresh token
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token},
        )

        assert response.status_code == 200
        data = response.json()

        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

        # Verify new tokens are different from original
        assert data["access_token"] != register_response.json()["access_token"]
        assert data["refresh_token"] != refresh_token

    def test_refresh_with_access_token_fails(self, client: TestClient):
        """Test that using access token for refresh fails."""
        # Register and get tokens
        register_response = client.post(
            "/api/auth/register",
            json={
                "email": "wrongtoken@example.com",
                "password": "SecurePass123!",
            },
        )

        access_token = register_response.json()["access_token"]

        # Try to refresh with access token (should fail)
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": access_token},
        )

        assert response.status_code == 401
        assert "invalid token type" in response.json()["detail"].lower()

    def test_refresh_with_invalid_token(self, client: TestClient):
        """Test refresh with invalid token."""
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": "invalid.token.here"},
        )

        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()


class TestProtectedEndpoints:
    """Tests for protected endpoints requiring authentication."""

    def test_get_current_user(self, client: TestClient):
        """Test getting current user info."""
        # Register and get token
        register_response = client.post(
            "/api/auth/register",
            json={
                "email": "me@example.com",
                "password": "SecurePass123!",
                "full_name": "Me User",
            },
        )

        access_token = register_response.json()["access_token"]

        # Get current user
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 200
        user = response.json()

        assert user["email"] == "me@example.com"
        assert user["full_name"] == "Me User"
        assert user["is_active"] is True

    def test_get_current_user_without_token(self, client: TestClient):
        """Test getting current user without token fails."""
        response = client.get("/api/auth/me")

        assert response.status_code == 403  # No credentials provided

    def test_get_current_user_with_invalid_token(self, client: TestClient):
        """Test getting current user with invalid token."""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"},
        )

        assert response.status_code == 401

    def test_update_current_user(self, client: TestClient):
        """Test updating current user information."""
        # Register and get token
        register_response = client.post(
            "/api/auth/register",
            json={
                "email": "update@example.com",
                "password": "SecurePass123!",
                "full_name": "Old Name",
            },
        )

        access_token = register_response.json()["access_token"]

        # Update user
        response = client.put(
            "/api/auth/me?full_name=New Name",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 200
        user = response.json()

        assert user["full_name"] == "New Name"
        assert user["email"] == "update@example.com"

    def test_logout(self, client: TestClient):
        """Test logout endpoint."""
        # Register and get token
        register_response = client.post(
            "/api/auth/register",
            json={
                "email": "logout@example.com",
                "password": "SecurePass123!",
            },
        )

        access_token = register_response.json()["access_token"]

        # Logout
        response = client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 200
        assert "message" in response.json()


@pytest.mark.asyncio
async def test_password_hashing(db_session: AsyncSession):
    """Test that passwords are properly hashed."""
    from app.services.auth import AuthService

    auth_service = AuthService(db_session)

    # Register user
    await auth_service.register_user(
        email="hashtest@example.com",
        password="PlainPassword123!",
    )

    # Get user from database
    result = await db_session.execute(
        select(User).where(User.email == "hashtest@example.com")
    )
    user = result.scalar_one()

    # Verify password is hashed (not stored in plain text)
    assert user.hashed_password != "PlainPassword123!"

    # Verify password can be verified
    assert verify_password("PlainPassword123!", user.hashed_password)
    assert not verify_password("WrongPassword", user.hashed_password)


@pytest.mark.asyncio
async def test_token_expiration(db_session: AsyncSession):
    """Test that tokens have proper expiration."""
    from datetime import timedelta
    from app.services.auth import AuthService
    from app.core.security import decode_token
    from app.core.config import settings

    auth_service = AuthService(db_session)

    # Register user
    auth_response = await auth_service.register_user(
        email="expiry@example.com",
        password="SecurePass123!",
    )

    # Decode and verify access token expiration
    access_payload = decode_token(auth_response.access_token)
    assert access_payload is not None
    assert "exp" in access_payload
    assert access_payload["type"] == "access"

    # Decode and verify refresh token expiration
    refresh_payload = decode_token(auth_response.refresh_token)
    assert refresh_payload is not None
    assert "exp" in refresh_payload
    assert refresh_payload["type"] == "refresh"


@pytest.mark.asyncio
async def test_inactive_user_cannot_login(db_session: AsyncSession):
    """Test that inactive users cannot login."""
    from app.services.auth import AuthService

    auth_service = AuthService(db_session)

    # Register user
    await auth_service.register_user(
        email="inactive@example.com",
        password="SecurePass123!",
    )

    # Get user and set as inactive
    result = await db_session.execute(
        select(User).where(User.email == "inactive@example.com")
    )
    user = result.scalar_one()
    user.is_active = False
    db_session.add(user)
    await db_session.commit()

    # Try to login as inactive user
    with pytest.raises(Exception) as exc_info:
        await auth_service.login_user(
            email="inactive@example.com",
            password="SecurePass123!",
        )

    assert exc_info.value.status_code == 403
    assert "inactive" in str(exc_info.value.detail).lower()
