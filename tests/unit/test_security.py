"""
Unit tests for security utilities.
"""

import pytest

from app.core.security import (
    create_access_token,
    create_refresh_token,
    generate_api_key,
    get_password_hash,
    hash_api_key,
    verify_password,
    verify_token,
)


class TestPasswordHashing:
    """Tests for password hashing functions."""

    def test_hash_password(self):
        """Test password hashing."""
        password = "testpassword123"
        hashed = get_password_hash(password)

        assert hashed != password
        assert len(hashed) > 0

    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "testpassword123"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed = get_password_hash(password)

        assert verify_password(wrong_password, hashed) is False


class TestJWTTokens:
    """Tests for JWT token functions."""

    def test_create_access_token(self):
        """Test access token creation."""
        user_id = 123
        token = create_access_token(subject=user_id)

        assert token is not None
        assert len(token) > 0

    def test_create_refresh_token(self):
        """Test refresh token creation."""
        user_id = 123
        token = create_refresh_token(subject=user_id)

        assert token is not None
        assert len(token) > 0

    def test_verify_access_token_valid(self):
        """Test verifying valid access token."""
        user_id = 123
        token = create_access_token(subject=user_id)

        verified_user_id = verify_token(token, token_type="access")

        assert verified_user_id == str(user_id)

    def test_verify_refresh_token_valid(self):
        """Test verifying valid refresh token."""
        user_id = 123
        token = create_refresh_token(subject=user_id)

        verified_user_id = verify_token(token, token_type="refresh")

        assert verified_user_id == str(user_id)

    def test_verify_token_invalid(self):
        """Test verifying invalid token."""
        invalid_token = "invalid.token.string"

        verified_user_id = verify_token(invalid_token)

        assert verified_user_id is None

    def test_verify_token_wrong_type(self):
        """Test verifying token with wrong type."""
        user_id = 123
        access_token = create_access_token(subject=user_id)

        # Try to verify access token as refresh token
        verified_user_id = verify_token(access_token, token_type="refresh")

        assert verified_user_id is None


class TestAPIKeys:
    """Tests for API key functions."""

    def test_generate_api_key(self):
        """Test API key generation."""
        api_key = generate_api_key()

        assert api_key is not None
        assert len(api_key) > 0
        assert api_key.startswith("sk_")

    def test_hash_api_key(self):
        """Test API key hashing."""
        api_key = generate_api_key()
        hashed = hash_api_key(api_key)

        assert hashed != api_key
        assert len(hashed) > 0

    def test_verify_api_key_hash(self):
        """Test verifying API key with its hash."""
        api_key = generate_api_key()
        hashed = hash_api_key(api_key)

        # Hash the same key again and compare
        hashed2 = hash_api_key(api_key)

        assert hashed == hashed2

    def test_generate_unique_api_keys(self):
        """Test that generated API keys are unique."""
        key1 = generate_api_key()
        key2 = generate_api_key()

        assert key1 != key2
