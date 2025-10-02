# tests/conftest.py

import asyncio
import os
import sys

import pytest
import pytest_asyncio
from decimal import Decimal
from typing import AsyncGenerator, Generator

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from app.config import get_settings
from app.database import get_session
from app.main import app
from app.models import User, Product, Subscription, Notification
from app.services.auth import AuthService
from app.services.product import ProductService
from app.services.subscription import SubscriptionService

settings = get_settings()

# Set event loop policy for Windows
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def db_session(event_loop):
    """Fully isolated engine + session + cleanup (to be runnable on Windows)"""
    engine = create_async_engine(
        # os.getenv("DATABASE_URL").replace("postgresql://", "postgresql+asyncpg://"),
        settings.database_url.replace("postgresql://", "postgresql+asyncpg://"),
        echo=False,
        pool_pre_ping=True,
        pool_recycle=300,
    )
    async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # create tables
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)

    async with async_session_maker() as session:
        yield session  # tests

    # --- teardown ---
    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test client."""

    def get_test_session():
        return db_session

    app.dependency_overrides[get_session] = get_test_session

    from httpx import ASGITransport

    transport = ASGITransport(app=app)
    async with AsyncClient(
            transport=transport,
            base_url="http://test",
            follow_redirects=True,
    ) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create test user."""
    auth_service = AuthService(db_session)
    user = await auth_service.create_user(
        email="test@example.com",
        password="testpassword123"
    )
    return user


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession) -> User:
    """Create admin user."""
    auth_service = AuthService(db_session)
    user = await auth_service.create_user(
        email="admin@example.com",
        password="adminpassword123"
    )
    user.is_admin = True
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_product(db_session: AsyncSession) -> Product:
    """Create test product."""
    from app.schemas.product import ProductCreate

    product_service = ProductService(db_session)
    product_data = ProductCreate(
        url="https://example.com/product/123",
        title="Test Product",
        brand="Test Brand",
        current_price=Decimal("99.99"),
        currency="USD",
        store_name="test_store",
        external_id="test-123",
    )

    product = await product_service.create(product_data)
    return product


@pytest_asyncio.fixture
async def test_subscription(
        db_session: AsyncSession, test_user: User, test_product: Product
) -> Subscription:
    """Create test subscription."""
    from app.schemas.subscription import SubscriptionCreate

    subscription_service = SubscriptionService(db_session)
    subscription_data = SubscriptionCreate(
        product_id=test_product.id,
        subscription_type="product",
        price_threshold=Decimal("89.99"),
    )

    subscription = await subscription_service.create_subscription(
        user_id=test_user.id,
        subscription_data=subscription_data
    )
    return subscription


@pytest.fixture
def auth_headers(test_user: User) -> dict[str, str]:
    """Create authentication headers."""
    from app.core.security import create_access_token

    access_token = create_access_token(test_user.id)
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def admin_headers(admin_user: User) -> dict[str, str]:
    """Create admin authentication headers."""
    from app.core.security import create_access_token

    access_token = create_access_token(admin_user.id)
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def sample_scraped_data():
    """Sample scraped product data."""
    from app.scrapers.base import ScrapedProduct

    return ScrapedProduct(
        title="Sample Product",
        price=Decimal("49.99"),
        currency="USD",
        brand="Sample Brand",
        image_url="https://example.com/image.jpg",
        external_id="sample-123",
    )


@pytest.fixture
def mock_ebay_response():
    """Mock eBay API response."""
    return {
        "title": "iPhone 14 Pro Max",
        "price": {
            "value": "999.99",
            "currency": "USD"
        },
        "image": {
            "imageUrl": "https://example.com/iphone.jpg"
        },
        "localizedAspects": [
            {
                "name": "Brand",
                "value": "Apple"
            }
        ]
    }


@pytest.fixture
def mock_etsy_response():
    """Mock Etsy API response."""
    return {
        "title": "Handmade Necklace",
        "price": {
            "amount": 2999,  # In cents
            "divisor": 100,
            "currency_code": "USD"
        },
        "images": [
            {
                "url_570xN": "https://example.com/necklace.jpg"
            }
        ],
        "shop": {
            "shop_name": "HandmadeJewelry"
        },
        "description": "Beautiful handmade silver necklace"
    }


# Async test utilities
async def create_test_user_with_token(db_session: AsyncSession, email: str = None) -> tuple[User, str]:
    """Create test user and return user with token."""
    from app.core.security import create_access_token

    if not email:
        email = f"testuser-{asyncio.get_event_loop().time()}@example.com"

    auth_service = AuthService(db_session)
    user = await auth_service.create_user(email=email, password="testpassword123")
    token = create_access_token(user.id)

    return user, token
