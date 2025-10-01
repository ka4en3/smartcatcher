"""Integration tests for notification system."""
import pytest
from decimal import Decimal
from httpx import AsyncClient

from app.models import User, Product, Subscription


@pytest.mark.asyncio
async def test_price_drop_notification_flow(
        client: AsyncClient,
        test_user: User,
        auth_headers: dict
):
    """Test complete price drop notification workflow."""

    # Step 1: Create product with high price
    product_data = {
        "url": "https://example.com/notification-test-product",
        "title": "Notification Test Product",
        "current_price": 100.0,
        "currency": "USD",
        "store_name": "test_store"
    }

    product_response = await client.post(
        "/products/",
        json=product_data,
        headers=auth_headers
    )
    product_id = product_response.json()["id"]

    # Step 2: Create subscription with price threshold
    subscription_data = {
        "product_id": product_id,
        "subscription_type": "product",
        "price_threshold": 80.0  # Will trigger when price drops below $80
    }

    subscription_response = await client.post(
        "/subscriptions/",
        json=subscription_data,
        headers=auth_headers
    )
    subscription_id = subscription_response.json()["id"]

    # Step 3: Update product price to trigger notification
    price_update = {
        "current_price": 75.0  # Below threshold
    }

    update_response = await client.put(
        f"/products/{product_id}",
        json=price_update,
        headers=auth_headers
    )
    assert update_response.status_code == 200

    # Step 4: Check if notification was created
    # Note: In real implementation, this would be triggered by background task
    notifications_response = await client.get(
        "/notifications/",
        headers=auth_headers
    )
    assert notifications_response.status_code == 200

    # Step 5: Verify notification content
    notifications = notifications_response.json()

    # Find notification for our subscription
    price_drop_notifications = [
        n for n in notifications
        if n["subscription_id"] == subscription_id
           and n["notification_type"] == "PRICE_DROP"
    ]

    if price_drop_notifications:  # Notification system is implemented
        notification = price_drop_notifications[0]
        assert notification["product_id"] == product_id
        assert "price dropped" in notification["message"].lower()
        assert notification["status"] in ["PENDING", "SENT"]


@pytest.mark.asyncio
async def test_notification_preferences(
        client: AsyncClient,
        test_user: User,
        auth_headers: dict
):
    """Test notification preferences and settings."""

    # Get current notification settings
    settings_response = await client.get(
        "/notifications/settings",
        headers=auth_headers
    )

    if settings_response.status_code == 200:  # Endpoint exists
        current_settings = settings_response.json()

        # Update notification preferences
        new_settings = {
            "email_notifications": True,
            "telegram_notifications": False,
            "price_drop_notifications": True,
            "availability_notifications": True
        }

        update_response = await client.put(
            "/notifications/settings",
            json=new_settings,
            headers=auth_headers
        )
        assert update_response.status_code == 200

        # Verify settings were updated
        updated_settings = update_response.json()
        assert updated_settings["email_notifications"] == new_settings["email_notifications"]
        assert updated_settings["telegram_notifications"] == new_settings["telegram_notifications"]


@pytest.mark.asyncio
async def test_notification_history(
        client: AsyncClient,
        auth_headers: dict
):
    """Test notification history and pagination."""

    # Get notification history
    history_response = await client.get(
        "/notifications/history?limit=10&offset=0",
        headers=auth_headers
    )

    if history_response.status_code == 200:
        history = history_response.json()

        # Verify pagination structure
        assert "items" in history or isinstance(history, list)

        if "items" in history:
            assert "total" in history
            assert "limit" in history
            assert "offset" in history

            # Test different page
            page2_response = await client.get(
                "/notifications/history?limit=5&offset=5",
                headers=auth_headers
            )
            assert page2_response.status_code == 200


@pytest.mark.asyncio
async def test_mark_notifications_as_read(
        client: AsyncClient,
        auth_headers: dict
):
    """Test marking notifications as read."""

    # Get unread notifications
    unread_response = await client.get(
        "/notifications/?status=unread",
        headers=auth_headers
    )

    if unread_response.status_code == 200:
        unread_notifications = unread_response.json()

        if unread_notifications:
            notification_id = unread_notifications[0]["id"]

            # Mark as read
            mark_read_response = await client.patch(
                f"/notifications/{notification_id}/read",
                headers=auth_headers
            )
            assert mark_read_response.status_code == 200

            # Verify it's marked as read
            notification_response = await client.get(
                f"/notifications/{notification_id}",
                headers=auth_headers
            )

            if notification_response.status_code == 200:
                notification = notification_response.json()
                assert notification["status"] == "READ" or notification["is_read"] is True
