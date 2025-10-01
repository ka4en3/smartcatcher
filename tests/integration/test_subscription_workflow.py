"""Integration tests for subscription workflow."""
import pytest
from decimal import Decimal
from httpx import AsyncClient

from app.models import User, Product, Subscription


@pytest.mark.asyncio
async def test_complete_subscription_workflow(
        client: AsyncClient,
        test_user: User,
        test_product: Product,
        auth_headers: dict
):
    """Test complete subscription workflow: create -> list -> update -> delete."""

    # Step 1: Create subscription
    subscription_data = {
        "product_id": test_product.id,
        "subscription_type": "product",
        "price_threshold": 79.99,
        "percentage_threshold": 20.0
    }

    create_response = await client.post(
        "/subscriptions/",
        json=subscription_data,
        headers=auth_headers
    )
    assert create_response.status_code == 201

    subscription = create_response.json()
    assert subscription["product_id"] == test_product.id
    assert subscription["price_threshold"] == 79.99
    assert subscription["is_active"] is True
    subscription_id = subscription["id"]

    # Step 2: List user's subscriptions
    list_response = await client.get("/subscriptions/", headers=auth_headers)
    assert list_response.status_code == 200

    subscriptions = list_response.json()
    assert len(subscriptions) >= 1
    assert any(sub["id"] == subscription_id for sub in subscriptions)

    # Step 3: Get specific subscription
    get_response = await client.get(
        f"/subscriptions/{subscription_id}",
        headers=auth_headers
    )
    assert get_response.status_code == 200

    retrieved_subscription = get_response.json()
    assert retrieved_subscription["id"] == subscription_id
    assert retrieved_subscription["product_id"] == test_product.id

    # Step 4: Update subscription
    update_data = {
        "price_threshold": 69.99,
        "percentage_threshold": 25.0
    }

    update_response = await client.put(
        f"/subscriptions/{subscription_id}",
        json=update_data,
        headers=auth_headers
    )
    assert update_response.status_code == 200

    updated_subscription = update_response.json()
    assert updated_subscription["price_threshold"] == 69.99
    assert updated_subscription["percentage_threshold"] == 25.0

    # Step 5: Delete subscription (soft delete)
    delete_response = await client.delete(
        f"/subscriptions/{subscription_id}",
        headers=auth_headers
    )
    assert delete_response.status_code == 204

    # Step 6: Verify subscription is not accessible (soft deleted)
    get_deleted_response = await client.get(
        f"/subscriptions/{subscription_id}",
        headers=auth_headers
    )
    assert get_deleted_response.status_code == 404


@pytest.mark.asyncio
async def test_subscription_permissions(
        client: AsyncClient,
        test_user: User,
        test_product: Product,
        auth_headers: dict
):
    """Test subscription access permissions."""

    # Create subscription as test_user
    subscription_data = {
        "product_id": test_product.id,
        "subscription_type": "product",
        "price_threshold": 99.99
    }

    create_response = await client.post(
        "/subscriptions/",
        json=subscription_data,
        headers=auth_headers
    )
    subscription_id = create_response.json()["id"]

    # Create another user
    other_user_data = {
        "email": "otheruser@example.com",
        "password": "otherpassword123"
    }

    await client.post("/auth/register", json=other_user_data)

    # Login as other user
    login_response = await client.post(
        "/auth/login",
        data={
            "username": other_user_data["email"],
            "password": other_user_data["password"]
        }
    )
    other_tokens = login_response.json()
    other_headers = {"Authorization": f"Bearer {other_tokens['access_token']}"}

    # Other user should not be able to access first user's subscription
    get_response = await client.get(
        f"/subscriptions/{subscription_id}",
        headers=other_headers
    )
    assert get_response.status_code == 404  # Not found (due to user filtering)

    # Other user should not be able to update first user's subscription
    update_response = await client.put(
        f"/subscriptions/{subscription_id}",
        json={"price_threshold": 50.0},
        headers=other_headers
    )
    assert update_response.status_code == 404

    # Other user should not be able to delete first user's subscription
    delete_response = await client.delete(
        f"/subscriptions/{subscription_id}",
        headers=other_headers
    )
    assert delete_response.status_code == 404


@pytest.mark.asyncio
async def test_brand_subscription_workflow(
        client: AsyncClient,
        auth_headers: dict
):
    """Test brand-based subscription workflow."""

    # Create brand subscription
    brand_subscription_data = {
        "subscription_type": "brand",
        "brand_name": "Apple",
        "percentage_threshold": 15.0
    }

    create_response = await client.post(
        "/subscriptions/",
        json=brand_subscription_data,
        headers=auth_headers
    )
    assert create_response.status_code == 201

    subscription = create_response.json()
    assert subscription["subscription_type"] == "brand"
    assert subscription["brand_name"] == "Apple"
    assert subscription["product_id"] is None
    assert subscription["percentage_threshold"] == 15.0

    # List subscriptions should include brand subscription
    list_response = await client.get("/subscriptions/", headers=auth_headers)
    subscriptions = list_response.json()

    brand_subscriptions = [s for s in subscriptions if s["subscription_type"] == "brand"]
    assert len(brand_subscriptions) >= 1
    assert any(s["brand_name"] == "Apple" for s in brand_subscriptions)
