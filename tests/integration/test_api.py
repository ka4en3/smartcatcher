# tests/integration/test_api.py

import pytest
from decimal import Decimal
from httpx import AsyncClient

from app.models.user import User
from app.models.product import Product


@pytest.mark.asyncio
async def test_full_subscription_workflow(client: AsyncClient, admin_headers: dict):
    """Test full subscription workflow: register, login, create subscription, get notifications."""

    # 1. Register user
    user_data = {
        "email": "workflow@example.com",
        "password": "workflowpass123"
    }

    register_response = await client.post("/auth/register", json=user_data)
    assert register_response.status_code == 201
    user = register_response.json()

    # 2. Login
    login_data = {
        "username": user_data["email"],
        "password": user_data["password"]
    }

    login_response = await client.post("/auth/login", json=login_data)
    assert login_response.status_code == 200
    tokens = login_response.json()

    user_headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    # 3. Create product (as admin)
    product_data = {
        "url": "https://example.com/workflow-product",
        "title": "Workflow Test Product",
        "brand": "Test Brand",
        "current_price": 199.99,
        "currency": "USD",
        "store_name": "test_store"
    }

    product_response = await client.post("/products", json=product_data, headers=admin_headers)
    assert product_response.status_code == 201
    product = product_response.json()

    # 4. Create subscription
    subscription_data = {
        "product_id": product["id"],
        "subscription_type": "product",
        "price_threshold": 150.00
    }

    subscription_response = await client.post("/subscriptions", json=subscription_data, headers=user_headers)
    assert subscription_response.status_code == 201
    subscription = subscription_response.json()

    # 5. Verify subscription in user's list
    subscriptions_response = await client.get("/subscriptions", headers=user_headers)
    assert subscriptions_response.status_code == 200
    subscriptions = subscriptions_response.json()
    assert len(subscriptions) == 1
    assert subscriptions[0]["id"] == subscription["id"]

    # 6. Update product price (as admin) to trigger notification
    price_update = {
        "current_price": 149.99  # Below threshold
    }

    update_response = await client.patch(f"/products/{product['id']}", json=price_update, headers=admin_headers)
    assert update_response.status_code == 200

    # 7. Verify price history
    history_response = await client.get(f"/products/{product['id']}/price-history", headers=user_headers)
    assert history_response.status_code == 200
    history = history_response.json()
    # Should have at least initial price entry


@pytest.mark.asyncio
async def test_product_search_and_filter_integration(client: AsyncClient, admin_headers: dict, auth_headers: dict):
    """Test product search and filtering integration."""

    # Create multiple products
    products_data = [
        {
            "url": "https://example.com/iphone-14",
            "title": "iPhone 14 Pro Max",
            "brand": "Apple",
            "current_price": 999.99,
            "currency": "USD",
            "store_name": "apple_store"
        },
        {
            "url": "https://example.com/galaxy-s23",
            "title": "Samsung Galaxy S23",
            "brand": "Samsung",
            "current_price": 899.99,
            "currency": "USD",
            "store_name": "samsung_store"
        },
        {
            "url": "https://example.com/macbook-air",
            "title": "MacBook Air M2",
            "brand": "Apple",
            "current_price": 1299.99,
            "currency": "USD",
            "store_name": "apple_store"
        }
    ]

    created_products = []
    for product_data in products_data:
        response = await client.post("/products", json=product_data, headers=admin_headers)
        assert response.status_code == 201
        created_products.append(response.json())

    # Test search functionality
    search_response = await client.get("/products?search=iPhone", headers=auth_headers)
    assert search_response.status_code == 200
    search_results = search_response.json()
    assert len(search_results) == 1
    assert "iPhone" in search_results[0]["title"]

    # Test brand filtering
    brand_response = await client.get("/products?brand=Apple", headers=auth_headers)
    assert brand_response.status_code == 200
    brand_results = brand_response.json()
    assert len(brand_results) == 2
    assert all(product["brand"] == "Apple" for product in brand_results)

    # Test store filtering
    store_response = await client.get("/products?store=apple_store", headers=auth_headers)
    assert store_response.status_code == 200
    store_results = store_response.json()
    assert len(store_results) == 2

    # Test pagination
    page1_response = await client.get("/products?limit=2", headers=auth_headers)
    assert page1_response.status_code == 200
    page1_results = page1_response.json()
    assert len(page1_results) <= 2

    page2_response = await client.get("/products?skip=2&limit=2", headers=auth_headers)
    assert page2_response.status_code == 200
    page2_results = page2_response.json()

    # Ensure no overlap between pages
    page1_ids = {p["id"] for p in page1_results}
    page2_ids = {p["id"] for p in page2_results}
    assert page1_ids.isdisjoint(page2_ids)


@pytest.mark.asyncio
async def test_subscription_management_flow(client: AsyncClient, test_product: Product, auth_headers: dict):
    """Test complete subscription management flow."""

    # 1. Create subscription
    subscription_data = {
        "product_id": test_product.id,
        "subscription_type": "product",
        "price_threshold": 89.99,
        "percentage_threshold": 10.0
    }

    create_response = await client.post("/subscriptions", json=subscription_data, headers=auth_headers)
    assert create_response.status_code == 201
    subscription = create_response.json()
    subscription_id = subscription["id"]

    # 2. Verify subscription exists
    get_response = await client.get(f"/subscriptions/{subscription_id}", headers=auth_headers)
    assert get_response.status_code == 200
    retrieved_subscription = get_response.json()
    assert retrieved_subscription["id"] == subscription_id

    # 3. Update subscription
    update_data = {
        "price_threshold": 79.99,
        "percentage_threshold": 15.0
    }

    update_response = await client.patch(f"/subscriptions/{subscription_id}", json=update_data, headers=auth_headers)
    assert update_response.status_code == 200
    updated_subscription = update_response.json()
    assert float(updated_subscription["price_threshold"]) == 79.99
    assert updated_subscription["percentage_threshold"] == 15.0

    # 4. List subscriptions
    list_response = await client.get("/subscriptions", headers=auth_headers)
    assert list_response.status_code == 200
    subscriptions = list_response.json()
    assert len(subscriptions) >= 1
    assert any(sub["id"] == subscription_id for sub in subscriptions)

    # 5. Delete subscription
    delete_response = await client.delete(f"/subscriptions/{subscription_id}", headers=auth_headers)
    assert delete_response.status_code == 204

    # 6. Verify subscription is gone
    get_deleted_response = await client.get(f"/subscriptions/{subscription_id}", headers=auth_headers)
    assert get_deleted_response.status_code == 404


@pytest.mark.asyncio
async def test_user_profile_management(client: AsyncClient):
    """Test user profile management flow."""

    # 1. Register user
    register_data = {
        "email": "profile@example.com",
        "password": "profilepass123"
    }

    register_response = await client.post("/auth/register", json=register_data)
    assert register_response.status_code == 201

    # 2. Login
    login_data = {
        "username": register_data["email"],
        "password": register_data["password"]
    }

    login_response = await client.post("/auth/login", json=login_data)
    assert login_response.status_code == 200
    tokens = login_response.json()

    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    # 3. Get current profile
    profile_response = await client.get("/users/me", headers=headers)
    assert profile_response.status_code == 200
    profile = profile_response.json()
    assert profile["email"] == register_data["email"]
    assert not profile["is_admin"]
    assert profile["is_active"]

    # 4. Update profile
    update_data = {
        "telegram_user_id": 123456789,
        "telegram_username": "testuser"
    }

    update_response = await client.patch("/users/me", json=update_data, headers=headers)
    assert update_response.status_code == 200
    updated_profile = update_response.json()
    assert updated_profile["telegram_user_id"] == 123456789
    assert updated_profile["telegram_username"] == "testuser"

    # 5. Refresh token
    refresh_data = {
        "refresh_token": tokens["refresh_token"]
    }

    refresh_response = await client.post("/auth/refresh", json=refresh_data)
    assert refresh_response.status_code == 200
    new_tokens = refresh_response.json()
    assert "access_token" in new_tokens
    assert "refresh_token" in new_tokens


@pytest.mark.asyncio
async def test_brand_subscription_workflow(client: AsyncClient, admin_headers: dict, auth_headers: dict):
    """Test brand subscription workflow."""

    # 1. Create products from same brand
    brand_name = "TestBrand"
    products_data = [
        {
            "url": "https://example.com/brand-product-1",
            "title": "TestBrand Product 1",
            "brand": brand_name,
            "current_price": 99.99,
            "currency": "USD",
            "store_name": "test_store"
        },
        {
            "url": "https://example.com/brand-product-2",
            "title": "TestBrand Product 2",
            "brand": brand_name,
            "current_price": 149.99,
            "currency": "USD",
            "store_name": "test_store"
        }
    ]

    created_products = []
    for product_data in products_data:
        response = await client.post("/products", json=product_data, headers=admin_headers)
        assert response.status_code == 201
        created_products.append(response.json())

    # 2. Create brand subscription
    subscription_data = {
        "subscription_type": "brand",
        "brand_name": brand_name,
        "price_threshold": 120.00,
        "percentage_threshold": 20.0
    }

    subscription_response = await client.post("/subscriptions", json=subscription_data, headers=auth_headers)
    assert subscription_response.status_code == 201
    subscription = subscription_response.json()
    assert subscription["brand_name"] == brand_name
    assert subscription["subscription_type"] == "brand"

    # 3. Verify subscription in list
    list_response = await client.get("/subscriptions", headers=auth_headers)
    assert list_response.status_code == 200
    subscriptions = list_response.json()
    brand_subscriptions = [sub for sub in subscriptions if sub["subscription_type"] == "brand"]
    assert len(brand_subscriptions) >= 1

    # 4. Test product filtering by brand
    brand_products_response = await client.get(f"/products?brand={brand_name}", headers=auth_headers)
    assert brand_products_response.status_code == 200
    brand_products = brand_products_response.json()
    assert len(brand_products) == 2
    assert all(product["brand"] == brand_name for product in brand_products)


@pytest.mark.asyncio
async def test_error_handling_and_validation(client: AsyncClient, auth_headers: dict):
    """Test API error handling and validation."""

    # Test invalid JSON
    response = await client.post("/auth/register", content="invalid json", headers={"Content-Type": "application/json"})
    assert response.status_code == 422

    # Test missing required fields
    incomplete_data = {"email": "test@example.com"}  # Missing password
    response = await client.post("/auth/register", json=incomplete_data)
    assert response.status_code == 422

    # Test invalid email format
    invalid_email_data = {"email": "not-an-email", "password": "password123"}
    response = await client.post("/auth/register", json=invalid_email_data)
    assert response.status_code == 422

    # Test accessing non-existent resources
    response = await client.get("/products/999999", headers=auth_headers)
    assert response.status_code == 404

    response = await client.get("/subscriptions/999999", headers=auth_headers)
    assert response.status_code == 404

    # Test unauthorized access
    response = await client.get("/products")
    assert response.status_code == 401

    # Test invalid subscription data
    invalid_subscription = {
        "subscription_type": "product"
        # Missing required fields
    }
    response = await client.post("/subscriptions", json=invalid_subscription, headers=auth_headers)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_pagination_and_limits(client: AsyncClient, admin_headers: dict, auth_headers: dict):
    """Test pagination limits and edge cases."""

    # Create multiple products for pagination testing
    for i in range(15):  # Create more than default page size
        product_data = {
            "url": f"https://example.com/pagination-product-{i}",
            "title": f"Pagination Test Product {i}",
            "brand": "PaginationBrand",
            "current_price": 10.00 + i,
            "currency": "USD",
            "store_name": "pagination_store"
        }

        response = await client.post("/products", json=product_data, headers=admin_headers)
        assert response.status_code == 201

    # Test default pagination
    response = await client.get("/products", headers=auth_headers)
    assert response.status_code == 200
    products = response.json()
    assert len(products) <= 100  # Default limit

    # Test custom limit
    response = await client.get("/products?limit=5", headers=auth_headers)
    assert response.status_code == 200
    products = response.json()
    assert len(products) <= 5

    # Test skip parameter
    response = await client.get("/products?skip=5&limit=5", headers=auth_headers)
    assert response.status_code == 200
    products = response.json()
    assert len(products) <= 5

    # Test maximum limit enforcement
    response = await client.get("/products?limit=1001", headers=auth_headers)
    assert response.status_code == 422

    # Test negative values
    response = await client.get("/products?skip=-1", headers=auth_headers)
    assert response.status_code == 422  # Should validate negative skip

    response = await client.get("/products?limit=0", headers=auth_headers)
    assert response.status_code == 422  # Should validate zero limit
