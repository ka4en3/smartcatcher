# tests/test_auth.py

import pytest
from httpx import AsyncClient

from app.models.user import User


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient):
    """Test user registration."""
    user_data = {
        "email": "newuser@example.com",
        "password": "newpassword123"
    }

    response = await client.post("/auth/register", json=user_data)
    assert response.status_code == 201

    data = response.json()
    assert data["email"] == user_data["email"]
    assert "id" in data
    assert "hashed_password" not in data  # Should not return password


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient, test_user: User):
    """Test registration with duplicate email."""
    user_data = {
        "email": test_user.email,
        "password": "newpassword123"
    }

    response = await client.post("/auth/register", json=user_data)
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, test_user: User):
    """Test successful login."""
    login_data = {
        "username": test_user.email,
        "password": "testpassword123"
    }

    response = await client.post("/auth/login", json=login_data)
    assert response.status_code == 200

    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient, test_user: User):
    """Test login with invalid credentials."""
    login_data = {
        "username": test_user.email,
        "password": "wrongpassword"
    }

    response = await client.post("/auth/login", json=login_data)
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    """Test login with nonexistent user."""
    login_data = {
        "username": "nonexistent@example.com",
        "password": "password123"
    }

    response = await client.post("/auth/login", json=login_data)
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]


@pytest.mark.asyncio
async def test_refresh_token(client: AsyncClient, test_user: User):
    """Test token refresh."""
    # First login to get tokens
    login_data = {
        "username": test_user.email,
        "password": "testpassword123"
    }

    login_response = await client.post("/auth/login", json=login_data)
    tokens = login_response.json()

    # Refresh tokens
    refresh_data = {
        "refresh_token": tokens["refresh_token"]
    }
    response = await client.post("/auth/refresh", json=refresh_data)
    assert response.status_code == 200

    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_refresh_invalid_token(client: AsyncClient):
    """Test refresh with invalid token."""
    refresh_data = {
        "refresh_token": "invalid_token"
    }

    response = await client.post("/auth/refresh", json=refresh_data)
    assert response.status_code == 401
    assert "Invalid refresh token" in response.json()["detail"]
