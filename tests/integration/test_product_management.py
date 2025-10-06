"""Integration tests for product management."""
from time import sleep

import pytest
from decimal import Decimal
from httpx import AsyncClient

from app.config import get_settings
from app.models import User

settings = get_settings()


# @pytest.mark.asyncio
# async def test_product_lifecycle(client: AsyncClient, auth_headers: dict, admin_headers: dict):
#     """Test complete product management lifecycle."""
#
#     # Step 1: Create product
#     product_data = {
#         "url": "https://example.com/integration-test-product",
#         "title": "Integration Test Product",
#         "brand": "TestBrand",
#         "current_price": 199.99,
#         "currency": "USD",
#         "store_name": "integration_store",
#         "external_id": "integration-test-123",
#         "image_url": "https://example.com/product-image.jpg"
#     }
#
#     create_response = await client.post(
#         "/products",
#         json=product_data,
#         headers=admin_headers
#     )
#     assert create_response.status_code == 201
#
#     product = create_response.json()
#     product_id = product["id"]
#     assert product["title"] == product_data["title"]
#     assert float(product["current_price"]) == product_data["current_price"]
#
#     # Step 2: Get product by ID
#     get_response = await client.get(
#         f"/products/{product_id}",
#         headers=auth_headers
#     )
#     assert get_response.status_code == 200
#
#     retrieved_product = get_response.json()
#     assert retrieved_product["id"] == product_id
#     assert retrieved_product["url"] == product_data["url"]
#
#     # Step 3: Update product
#     update_data = {
#         "current_price": 179.99,
#         "title": "Updated Integration Test Product"
#     }
#
#     update_response = await client.patch(
#         f"/products/{product_id}",
#         json=update_data,
#         headers=admin_headers
#     )
#     assert update_response.status_code == 200
#
#     updated_product = update_response.json()
#     assert float(updated_product["current_price"]) == 179.99
#     assert updated_product["title"] == update_data["title"]
#
#     # Step 4: Search for product
#     search_response = await client.get(
#         "/products?search=Integration Test",
#         headers=auth_headers
#     )
#     assert search_response.status_code == 200
#
#     search_results = search_response.json()
#     assert len(search_results) >= 1
#     assert any(p["id"] == product_id for p in search_results)
#
#     # Step 5: Get products by brand
#     brand_response = await client.get(
#         f"/products?brand={product_data['brand']}",
#         headers=auth_headers
#     )
#     assert brand_response.status_code == 200
#
#     brand_products = brand_response.json()
#     assert len(brand_products) >= 1
#     assert any(p["id"] == product_id for p in brand_products)


# @pytest.mark.asyncio
# async def test_product_price_history(client: AsyncClient, auth_headers: dict, admin_headers: dict):
#     """Test product price history tracking."""
#
#     # Create product with initial price
#     product_data = {
#         "url": "http://demo.com",
#         "title": "Price History Test Product",
#         "current_price": 100.0,
#         "currency": "USD",
#         "store_name": "demo"
#     }
#
#     create_response = await client.post(
#         "/products",
#         json=product_data,
#         headers=admin_headers
#     )
#     print(create_response.json())
#     assert create_response.status_code == 201
#     product_id = create_response.json()["id"]
#
#     # Update price multiple times
#     price_updates = [90.0, 85.0, 95.0, 80.0]
#
#     for new_price in price_updates:
#         update_response = await client.patch(
#             f"/products/{product_id}",
#             json={"current_price": new_price},
#             headers=admin_headers
#         )
#         assert update_response.status_code == 200
#         sleep(settings.price_check_interval_seconds + 1)
#
#     # Get price history
#     history_response = await client.get(
#         f"/products/{product_id}/price-history",
#         headers=auth_headers
#     )
#     assert history_response.status_code == 200
#
#     price_history = history_response.json()
#     assert len(price_history) >= len(price_updates)
#
#     # Verify price progression
#     prices = [float(entry["price"]) for entry in price_history]
#     assert 100.0 in prices  # Initial price should be recorded


# @pytest.mark.asyncio
# async def test_product_validation(client: AsyncClient, auth_headers: dict, admin_headers: dict):
#     """Test product data validation."""
#
#     # Test invalid URL format
#     invalid_url_data = {
#         "url": "not-a-valid-url",
#         "title": "Test Product",
#         "current_price": 50.0,
#         "currency": "USD",
#         "store_name": "test_store"
#     }
#
#     response = await client.post(
#         "/products",
#         json=invalid_url_data,
#         headers=admin_headers
#     )
#     assert response.status_code == 422
#
#     # Test negative price
#     negative_price_data = {
#         "url": "https://example.com/product",
#         "title": "Test Product",
#         "current_price": -10.0,
#         "currency": "USD",
#         "store_name": "test_store"
#     }
#
#     response = await client.post(
#         "/products",
#         json=negative_price_data,
#         headers=admin_headers
#     )
#     assert response.status_code == 422
#
#     # Test invalid currency
#     invalid_currency_data = {
#         "url": "https://example.com/product",
#         "title": "Test Product",
#         "current_price": 50.0,
#         "currency": "INVALID",
#         "store_name": "test_store"
#     }
#
#     response = await client.post(
#         "/products",
#         json=invalid_currency_data,
#         headers=admin_headers
#     )
#     assert response.status_code == 422
#
#
# @pytest.mark.asyncio
# async def test_duplicate_product_handling(client: AsyncClient, auth_headers: dict, admin_headers: dict):
#     """Test handling of duplicate product URLs."""
#
#     product_data = {
#         "url": "https://example.com/duplicate-test-product",
#         "title": "Duplicate Test Product",
#         "current_price": 75.0,
#         "currency": "USD",
#         "store_name": "test_store"
#     }
#
#     # Create first product
#     first_response = await client.post(
#         "/products",
#         json=product_data,
#         headers=admin_headers
#     )
#     assert first_response.status_code == 201
#     first_product = first_response.json()
#
#     # Try to create duplicate product with same URL
#     second_response = await client.post(
#         "/products",
#         json=product_data,
#         headers=admin_headers
#     )
#     assert second_response.status_code == 201  # return the same product
#
#     second_product = second_response.json()
#     assert second_product["id"] == first_product["id"]


@pytest.mark.asyncio
async def test_create_or_get_product_by_url(client: AsyncClient, auth_headers: dict):
    payload = {"url": "https://example.com/product/123"}
    r1 = await client.post("/products/by-url", json=payload, headers=auth_headers)

    print(r1.json())

    assert r1.status_code == 201
    p1 = r1.json()
    assert p1["url"] == payload["url"]

    # second request should return the same product
    r2 = await client.post("/products/by-url", json=payload, headers=auth_headers)
    assert r2.status_code in (200, 201)
    p2 = r2.json()
    assert p1["id"] == p2["id"]
