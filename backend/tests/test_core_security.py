"""Tests for security utilities."""

import pytest
from datetime import timedelta

from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
)


class TestPasswordHashing:
    """Tests for password hashing functions."""

    def test_hash_password(self):
        """Test password hashing."""
        password = "MySecurePassword123!"
        hashed = get_password_hash(password)

        assert hashed != password
        assert len(hashed) > 0
        assert hashed.startswith("$2")  # bcrypt prefix

    def test_verify_password_success(self):
        """Test password verification with correct password."""
        password = "MySecurePassword123!"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_failure(self):
        """Test password verification with wrong password."""
        password = "MySecurePassword123!"
        hashed = get_password_hash(password)

        assert verify_password("WrongPassword", hashed) is False

    def test_same_password_different_hashes(self):
        """Test that same password generates different hashes (due to salt)."""
        password = "MySecurePassword123!"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        assert hash1 != hash2
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)

    def test_long_password_truncation(self):
        """Test that passwords longer than 72 bytes are handled correctly."""
        # Create a password longer than 72 bytes
        long_password = "A" * 100
        hashed = get_password_hash(long_password)

        # Should still verify correctly
        assert verify_password(long_password, hashed)


class TestJWTTokens:
    """Tests for JWT token creation and verification."""

    def test_create_access_token(self):
        """Test access token creation."""
        data = {"sub": "user123"}
        token = create_access_token(data)

        assert isinstance(token, str)
        assert len(token) > 0

        # Decode and verify
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == "user123"
        assert payload["type"] == "access"
        assert "exp" in payload

    def test_create_access_token_with_custom_expiry(self):
        """Test access token with custom expiration."""
        data = {"sub": "user123"}
        expires_delta = timedelta(minutes=15)
        token = create_access_token(data, expires_delta)

        payload = decode_token(token)
        assert payload is not None
        assert payload["type"] == "access"

    def test_create_refresh_token(self):
        """Test refresh token creation."""
        data = {"sub": "user123"}
        token = create_refresh_token(data)

        assert isinstance(token, str)
        assert len(token) > 0

        # Decode and verify
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == "user123"
        assert payload["type"] == "refresh"
        assert "exp" in payload

    def test_decode_valid_token(self):
        """Test decoding a valid token."""
        data = {"sub": "user123", "extra": "data"}
        token = create_access_token(data)

        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == "user123"
        assert payload["extra"] == "data"

    def test_decode_invalid_token(self):
        """Test decoding an invalid token."""
        payload = decode_token("invalid.token.here")
        assert payload is None

    def test_decode_malformed_token(self):
        """Test decoding a malformed token."""
        payload = decode_token("not-even-a-jwt")
        assert payload is None

    def test_token_type_differentiation(self):
        """Test that access and refresh tokens have different types."""
        data = {"sub": "user123"}
        access_token = create_access_token(data)
        refresh_token = create_refresh_token(data)

        access_payload = decode_token(access_token)
        refresh_payload = decode_token(refresh_token)

        assert access_payload["type"] == "access"
        assert refresh_payload["type"] == "refresh"

    def test_tokens_are_unique(self):
        """Test that multiple tokens for same data are different."""
        data = {"sub": "user123"}
        token1 = create_access_token(data)
        token2 = create_access_token(data)

        # Tokens should be different due to different expiration timestamps
        assert token1 != token2

        # But both should decode to valid payloads
        payload1 = decode_token(token1)
        payload2 = decode_token(token2)
        assert payload1 is not None
        assert payload2 is not None
        assert payload1["sub"] == payload2["sub"]
