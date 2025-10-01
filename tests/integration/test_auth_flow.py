"""Integration tests for authentication flow."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User


@pytest.mark.asyncio
async def test_complete_auth_flow(client: AsyncClient, db_session: AsyncSession):
    """Test complete authentication flow: register -> login -> access protected route."""

    # Step 1: Register new user
    register_data = {
        "email": "integration_test@example.com",
        "password": "integration_password123"
    }

    register_response = await client.post("/auth/register", json=register_data)
    assert register_response.status_code == 201

    register_result = register_response.json()
    assert register_result["email"] == register_data["email"]
    assert "id" in register_result
    user_id = register_result["id"]

    # Step 2: Login with created user
    login_data = {
        "username": register_data["email"],  # OAuth2 uses 'username' field
        "password": register_data["password"]
    }

    login_response = await client.post("/auth/login", data=login_data)
    assert login_response.status_code == 200

    tokens = login_response.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert tokens["token_type"] == "bearer"

    # Step 3: Access protected route with token
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    profile_response = await client.get("/users/me", headers=headers)
    assert profile_response.status_code == 200

    profile_data = profile_response.json()
    assert profile_data["id"] == user_id
    assert profile_data["email"] == register_data["email"]
    assert profile_data["is_active"] is True


@pytest.mark.asyncio
async def test_token_refresh_flow(client: AsyncClient, test_user: User):
    """Test token refresh flow."""

    # Step 1: Login to get initial tokens
    login_data = {
        "username": test_user.email,
        "password": "testpassword123"
    }

    login_response = await client.post("/auth/login", data=login_data)
    tokens = login_response.json()

    # Step 2: Use refresh token to get new tokens
    refresh_data = {
        "refresh_token": tokens["refresh_token"]
    }

    refresh_response = await client.post("/auth/refresh", json=refresh_data)
    assert refresh_response.status_code == 200

    new_tokens = refresh_response.json()
    assert "access_token" in new_tokens
    assert "refresh_token" in new_tokens

    # New tokens should be different from original
    assert new_tokens["access_token"] != tokens["access_token"]

    # Step 3: Old token should still work (for a grace period)
    old_headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    profile_response = await client.get("/users/me", headers=old_headers)
    assert profile_response.status_code == 200

    # Step 4: New token should work
    new_headers = {"Authorization": f"Bearer {new_tokens['access_token']}"}
    profile_response = await client.get("/users/me", headers=new_headers)
    assert profile_response.status_code == 200


@pytest.mark.asyncio
async def test_invalid_token_handling(client: AsyncClient):
    """Test handling of invalid tokens."""

    invalid_tokens = [
        "invalid.token.here",
        "Bearer invalid_token",
        "",
        "expired.token.payload"
    ]

    for invalid_token in invalid_tokens:
        headers = {"Authorization": f"Bearer {invalid_token}"}
        response = await client.get("/users/me", headers=headers)
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_duplicate_registration(client: AsyncClient, test_user: User):
    """Test duplicate email registration."""

    # Try to register with existing email
    duplicate_data = {
        "email": test_user.email,
        "password": "different_password123"
    }

    response = await client.post("/auth/register", json=duplicate_data)
    assert response.status_code == 400

    error_data = response.json()
    assert "email already registered" in error_data["detail"].lower()
