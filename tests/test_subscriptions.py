# tests/test_subscriptions.py

import pytest
from decimal import Decimal
from httpx import AsyncClient

from app.models.user import User
from app.models.product import Product
from app.models.subscription import Subscription


@pytest.mark.asyncio
async def test_create_subscription(client: AsyncClient, test_user: User, test_product: Product, auth_headers: dict):
    """Test creating subscription."""
    subscription_data = {
        "product_id": test_product.id,
        "subscription_type": "product",
        "price_threshold": 79.99
    }

    response = await client.post("/subscriptions", json=subscription_data, headers=auth_headers)
    assert response.status_code == 201

    data = response.json()
    assert data["product_id"] == test_product.id
    assert data["user_id"] == test_user.id
    assert float(data["price_threshold"]) == subscription_data["price_threshold"]


@pytest.mark.asyncio
async def test_create_brand_subscription(client: AsyncClient, test_user: User, auth_headers: dict):
    """Test creating brand subscription."""
    subscription_data = {
        "subscription_type": "brand",
        "brand_name": "Nike",
        "price_threshold": 100.00,
        "percentage_threshold": 20.0
    }

    response = await client.post("/subscriptions", json=subscription_data, headers=auth_headers)
    assert response.status_code == 201

    data = response.json()
    assert data["brand_name"] == "Nike"
    assert data["user_id"] == test_user.id
    assert data["subscription_type"] == "brand"


@pytest.mark.asyncio
async def test_create_subscription_by_url(client: AsyncClient, test_user: User, test_product: Product, auth_headers: dict):
    """Test creating subscription by product URL."""
    subscription_data = {
        "product_url": test_product.url,
        "subscription_type": "product",
        "price_threshold": 89.99
    }

    response = await client.post("/subscriptions", json=subscription_data, headers=auth_headers)
    assert response.status_code == 201

    data = response.json()
    assert data["product_id"] == test_product.id


@pytest.mark.asyncio
async def test_create_subscription_invalid_data(client: AsyncClient, auth_headers: dict):
    """Test creating subscription with invalid data."""
    # Missing required fields
    subscription_data = {
        "subscription_type": "product"
        # Missing product_id/url and thresholds
    }

    response = await client.post("/subscriptions", json=subscription_data, headers=auth_headers)
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_list_user_subscriptions(client: AsyncClient, test_subscription: Subscription, auth_headers: dict):
    """Test listing user subscriptions."""
    response = await client.get("/subscriptions", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["id"] == test_subscription.id


@pytest.mark.asyncio
async def test_get_subscription_by_id(client: AsyncClient, test_subscription: Subscription, auth_headers: dict):
    """Test getting subscription by ID."""
    response = await client.get(f"/subscriptions/{test_subscription.id}", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == test_subscription.id
    assert data["product_id"] == test_subscription.product_id


@pytest.mark.asyncio
async def test_get_other_user_subscription(client: AsyncClient, test_subscription: Subscription):
    """Test getting other user's subscription (should be forbidden)."""
    # Create different user
    from tests.conftest import create_test_user_with_token
    from app.database import async_session_maker

    async with async_session_maker() as session:
        other_user, other_token = await create_test_user_with_token(session)
        other_headers = {"Authorization": f"Bearer {other_token}"}

    response = await client.get(f"/subscriptions/{test_subscription.id}", headers=other_headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_subscription(client: AsyncClient, test_subscription: Subscription, auth_headers: dict):
    """Test updating subscription."""
    update_data = {
        "price_threshold": 69.99,
        "percentage_threshold": 15.0
    }

    response = await client.patch(f"/subscriptions/{test_subscription.id}", json=update_data, headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert float(data["price_threshold"]) == update_data["price_threshold"]
    assert data["percentage_threshold"] == update_data["percentage_threshold"]


@pytest.mark.asyncio
async def test_delete_subscription(client: AsyncClient, test_subscription: Subscription, auth_headers: dict):
    """Test deleting subscription."""
    response = await client.delete(f"/subscriptions/{test_subscription.id}", headers=auth_headers)
    assert response.status_code == 204

    # Verify subscription is gone
    response = await client.get(f"/subscriptions/{test_subscription.id}", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_nonexistent_subscription(client: AsyncClient, auth_headers: dict):
    """Test deleting nonexistent subscription."""
    response = await client.delete("/subscriptions/999999", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_subscriptions_pagination(client: AsyncClient, test_subscription: Subscription, auth_headers: dict):
    """Test subscription listing pagination."""
    response = await client.get("/subscriptions?skip=0&limit=1", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 1


@pytest.mark.asyncio
async def test_subscriptions_filter_active(client: AsyncClient, test_subscription: Subscription, auth_headers: dict):
    """Test filtering active subscriptions."""
    # Test active only (default)
    response = await client.get("/subscriptions?active_only=true", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert all(sub["is_active"] for sub in data)

    # Test including inactive
    response = await client.get("/subscriptions?active_only=false", headers=auth_headers)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_subscriptions_unauthorized(client: AsyncClient, test_subscription: Subscription):
    """Test accessing subscriptions without authentication."""
    response = await client.get("/subscriptions")
    assert response.status_code == 401
