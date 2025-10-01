# tests/test_products.py

import pytest
from decimal import Decimal
from httpx import AsyncClient

from app.models.user import User
from app.models.product import Product


@pytest.mark.asyncio
async def test_list_products(client: AsyncClient, test_product: Product, auth_headers: dict):
    """Test listing products."""
    response = await client.get("/products", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["id"] == test_product.id


@pytest.mark.asyncio
async def test_get_product_by_id(client: AsyncClient, test_product: Product, auth_headers: dict):
    """Test getting product by ID."""
    response = await client.get(f"/products/{test_product.id}", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == test_product.id
    assert data["title"] == test_product.title
    assert data["url"] == test_product.url


@pytest.mark.asyncio
async def test_get_nonexistent_product(client: AsyncClient, auth_headers: dict):
    """Test getting nonexistent product."""
    response = await client.get("/products/999999", headers=auth_headers)
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_product_admin(client: AsyncClient, admin_headers: dict):
    """Test creating product as admin."""
    product_data = {
        "url": "https://example.com/new-product",
        "title": "New Test Product",
        "brand": "New Brand",
        "current_price": 149.99,
        "currency": "USD",
        "store_name": "new_store"
    }

    response = await client.post("/products", json=product_data, headers=admin_headers)
    assert response.status_code == 201

    data = response.json()
    assert data["title"] == product_data["title"]
    assert data["url"] == product_data["url"]
    assert float(data["current_price"]) == product_data["current_price"]


@pytest.mark.asyncio
async def test_create_product_duplicate_url(client: AsyncClient, test_product: Product, admin_headers: dict):
    """Test creating product with duplicate URL."""
    product_data = {
        "url": test_product.url,
        "title": "Duplicate URL Product",
        "brand": "Test Brand",
        "currency": "USD",
        "store_name": "test_store"
    }

    response = await client.post("/products", json=product_data, headers=admin_headers)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_product_non_admin(client: AsyncClient, auth_headers: dict):
    """Test creating product as non-admin user."""
    product_data = {
        "url": "https://example.com/forbidden-product",
        "title": "Forbidden Product",
        "brand": "Test Brand",
        "currency": "USD",
        "store_name": "test_store"
    }

    response = await client.post("/products", json=product_data, headers=auth_headers)
    assert response.status_code == 403
    assert "privileges" in response.json()["detail"]


@pytest.mark.asyncio
async def test_update_product_admin(client: AsyncClient, test_product: Product, admin_headers: dict):
    """Test updating product as admin."""
    update_data = {
        "title": "Updated Product Title",
        "current_price": 79.99
    }

    response = await client.patch(f"/products/{test_product.id}", json=update_data, headers=admin_headers)
    assert response.status_code == 200

    data = response.json()
    assert data["title"] == update_data["title"]
    assert float(data["current_price"]) == update_data["current_price"]


@pytest.mark.asyncio
async def test_get_product_price_history(client: AsyncClient, test_product: Product, auth_headers: dict):
    """Test getting product price history."""
    response = await client.get(f"/products/{test_product.id}/price-history", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    # Initially should be empty or have creation entry


@pytest.mark.asyncio
async def test_list_products_filtering(client: AsyncClient, test_product: Product, auth_headers: dict):
    """Test product listing with filters."""
    # Test search filter
    response = await client.get("/products?search=Test", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1

    # Test brand filter
    response = await client.get(f"/products?brand={test_product.brand}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1

    # Test store filter
    response = await client.get(f"/products?store={test_product.store_name}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_products_pagination(client: AsyncClient, test_product: Product, auth_headers: dict):
    """Test product listing pagination."""
    response = await client.get("/products?skip=0&limit=1", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 1


@pytest.mark.asyncio
async def test_products_unauthorized(client: AsyncClient, test_product: Product):
    """Test accessing products without authentication."""
    response = await client.get("/products")
    assert response.status_code == 401
