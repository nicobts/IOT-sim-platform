"""
Integration tests for authentication endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class TestAuthLogin:
    """Tests for login endpoint."""

    def test_login_success(self, client: TestClient, test_user: User):
        """Test successful login."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser",
                "password": "testpassword123",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client: TestClient, test_user: User):
        """Test login with wrong password."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser",
                "password": "wrongpassword",
            },
        )

        assert response.status_code == 401

    def test_login_nonexistent_user(self, client: TestClient):
        """Test login with non-existent user."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "nonexistent",
                "password": "password123",
            },
        )

        assert response.status_code == 401

    def test_login_missing_fields(self, client: TestClient):
        """Test login with missing fields."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser",
            },
        )

        assert response.status_code == 422  # Validation error


class TestAuthRefresh:
    """Tests for token refresh endpoint."""

    def test_refresh_token_success(self, client: TestClient, test_user: User):
        """Test successful token refresh."""
        # First, login to get tokens
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser",
                "password": "testpassword123",
            },
        )
        refresh_token = login_response.json()["refresh_token"]

        # Refresh the token
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    def test_refresh_token_invalid(self, client: TestClient):
        """Test token refresh with invalid token."""
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid.token.string"},
        )

        assert response.status_code == 401


class TestAuthMe:
    """Tests for get current user endpoint."""

    def test_get_current_user_success(
        self, client: TestClient, test_user: User, auth_headers: dict
    ):
        """Test getting current user."""
        response = client.get("/api/v1/auth/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "testuser@example.com"
        assert data["is_active"] is True
        assert data["is_superuser"] is False

    def test_get_current_user_unauthorized(self, client: TestClient):
        """Test getting current user without authentication."""
        response = client.get("/api/v1/auth/me")

        assert response.status_code == 401

    def test_get_current_user_invalid_token(self, client: TestClient):
        """Test getting current user with invalid token."""
        headers = {"Authorization": "Bearer invalid.token.string"}
        response = client.get("/api/v1/auth/me", headers=headers)

        assert response.status_code == 401


class TestAPIKeys:
    """Tests for API key management endpoints."""

    def test_create_api_key_success(
        self, client: TestClient, test_user: User, auth_headers: dict
    ):
        """Test creating API key."""
        response = client.post(
            "/api/v1/auth/api-keys",
            headers=auth_headers,
            json={
                "name": "Test API Key",
                "expires_in_days": 30,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "api_key" in data
        assert data["api_key"].startswith("sk_")
        assert data["name"] == "Test API Key"

    def test_create_api_key_without_expiration(
        self, client: TestClient, test_user: User, auth_headers: dict
    ):
        """Test creating API key without expiration."""
        response = client.post(
            "/api/v1/auth/api-keys",
            headers=auth_headers,
            json={
                "name": "Permanent Key",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["expires_at"] is None

    def test_list_api_keys(
        self, client: TestClient, test_user: User, auth_headers: dict
    ):
        """Test listing API keys."""
        # Create a key first
        client.post(
            "/api/v1/auth/api-keys",
            headers=auth_headers,
            json={"name": "Test Key"},
        )

        # List keys
        response = client.get("/api/v1/auth/api-keys", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_revoke_api_key(
        self, client: TestClient, test_user: User, auth_headers: dict
    ):
        """Test revoking API key."""
        # Create a key
        create_response = client.post(
            "/api/v1/auth/api-keys",
            headers=auth_headers,
            json={"name": "Key to Revoke"},
        )
        key_id = create_response.json()["id"]

        # Revoke the key
        response = client.delete(
            f"/api/v1/auth/api-keys/{key_id}",
            headers=auth_headers,
        )

        assert response.status_code == 200

    def test_revoke_nonexistent_api_key(
        self, client: TestClient, test_user: User, auth_headers: dict
    ):
        """Test revoking non-existent API key."""
        response = client.delete(
            "/api/v1/auth/api-keys/99999",
            headers=auth_headers,
        )

        assert response.status_code == 404


class TestUserRegistration:
    """Tests for user registration endpoint."""

    def test_register_user_as_superuser(
        self, client: TestClient, test_superuser: User, superuser_auth_headers: dict
    ):
        """Test user registration by superuser."""
        response = client.post(
            "/api/v1/auth/register",
            headers=superuser_auth_headers,
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "newpassword123",
                "is_superuser": False,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"

    def test_register_user_as_regular_user(
        self, client: TestClient, test_user: User, auth_headers: dict
    ):
        """Test that regular users cannot register new users."""
        response = client.post(
            "/api/v1/auth/register",
            headers=auth_headers,
            json={
                "username": "newuser2",
                "email": "newuser2@example.com",
                "password": "password123",
            },
        )

        assert response.status_code == 403  # Forbidden

    def test_register_duplicate_username(
        self, client: TestClient, test_superuser: User, superuser_auth_headers: dict
    ):
        """Test registering user with duplicate username."""
        response = client.post(
            "/api/v1/auth/register",
            headers=superuser_auth_headers,
            json={
                "username": "admin",  # Already exists
                "email": "another@example.com",
                "password": "password123",
            },
        )

        assert response.status_code == 400  # Bad request

    def test_register_duplicate_email(
        self, client: TestClient, test_superuser: User, superuser_auth_headers: dict
    ):
        """Test registering user with duplicate email."""
        response = client.post(
            "/api/v1/auth/register",
            headers=superuser_auth_headers,
            json={
                "username": "uniqueuser",
                "email": "admin@example.com",  # Already exists
                "password": "password123",
            },
        )

        assert response.status_code == 400  # Bad request
