"""Unit tests for service layer."""
import pytest
from unittest.mock import Mock, AsyncMock
from decimal import Decimal

from app.services.auth import AuthService
from app.services.product import ProductService
from app.services.user import UserService
from app.services.subscription import SubscriptionService
from app.models import User, Product, Subscription
from app.schemas.auth import UserRegister
from app.schemas.product import ProductCreate
from app.schemas.subscription import SubscriptionCreate


class TestAuthService:
    """Test authentication service."""

    @pytest.fixture
    def mock_session(self):
        """Mock database session."""
        return AsyncMock()

    @pytest.fixture
    def auth_service(self, mock_session):
        """Create auth service with mocked session."""
        return AuthService(mock_session)

    # @pytest.mark.asyncio
    # async def test_create_user(self, auth_service, mock_session):
    #     """Test user creation."""
    #     email = "test@example.com"
    #     password = "password123"
    #
    #     # Mock session behavior
    #     mock_session.add = Mock()
    #     mock_session.commit = AsyncMock()
    #     mock_session.refresh = AsyncMock()
    #
    #     user = await auth_service.create_user(email, password)
    #
    #     assert user.email == email
    #     assert user.is_active is True
    #     assert user.is_admin is False
    #     mock_session.add.assert_called_once()
    #     mock_session.commit.assert_called_once()
    #
    # @pytest.mark.asyncio
    # async def test_authenticate_user_success(self, auth_service, mock_session):
    #     """Test successful user authentication."""
    #     email = "test@example.com"
    #     password = "password123"
    #
    #     # Create a mock user with hashed password
    #     from app.core.security import get_password_hash
    #     hashed_password = get_password_hash(password)
    #
    #     mock_user = User(
    #         id=1,
    #         email=email,
    #         hashed_password=hashed_password,
    #         is_active=True
    #     )
    #
    #     # Mock database query
    #     mock_result = Mock()
    #     mock_result.scalar_one_or_none.return_value = mock_user
    #     mock_session.execute.return_value = mock_result
    #
    #     authenticated_user = await auth_service.authenticate_user(email, password)
    #
    #     assert authenticated_user == mock_user
    #     assert authenticated_user.email == email
    #
    # @pytest.mark.asyncio
    # async def test_authenticate_user_wrong_password(self, auth_service, mock_session):
    #     """Test authentication with wrong password."""
    #     email = "test@example.com"
    #     correct_password = "password123"
    #     wrong_password = "wrongpassword"
    #
    #     from app.core.security import get_password_hash
    #     hashed_password = get_password_hash(correct_password)
    #
    #     mock_user = User(
    #         id=1,
    #         email=email,
    #         hashed_password=hashed_password,
    #         is_active=True
    #     )
    #
    #     mock_result = Mock()
    #     mock_result.scalar_one_or_none.return_value = mock_user
    #     mock_session.execute.return_value = mock_result
    #
    #     authenticated_user = await auth_service.authenticate_user(email, wrong_password)
    #
    #     assert authenticated_user is None
    #
    # @pytest.mark.asyncio
    # async def test_authenticate_inactive_user(self, auth_service, mock_session):
    #     """Test authentication with inactive user."""
    #     email = "test@example.com"
    #     password = "password123"
    #
    #     from app.core.security import get_password_hash
    #     hashed_password = get_password_hash(password)
    #
    #     mock_user = User(
    #         id=1,
    #         email=email,
    #         hashed_password=hashed_password,
    #         is_active=False  # Inactive user
    #     )
    #
    #     mock_result = Mock()
    #     mock_result.scalar_one_or_none.return_value = mock_user
    #     mock_session.execute.return_value = mock_result
    #
    #     authenticated_user = await auth_service.authenticate_user(email, password)
    #
    #     assert authenticated_user is not None
    #     assert authenticated_user.is_active is False


class TestProductService:
    """Test product service."""

    @pytest.fixture
    def mock_session(self):
        return AsyncMock()

    @pytest.fixture
    def product_service(self, mock_session):
        return ProductService(mock_session)

    # @pytest.mark.asyncio
    # async def test_create_product(self, product_service, mock_session):
    #     """Test product creation."""
    #     product_data = ProductCreate(
    #         url="https://example.com/product",
    #         title="Test Product",
    #         brand="Test Brand",
    #         current_price=Decimal("99.99"),
    #         currency="USD",
    #         store_name="test_store",
    #         external_id="test-123"
    #     )
    #
    #     mock_session.add = Mock()
    #     mock_session.commit = AsyncMock()
    #     mock_session.refresh = AsyncMock()
    #
    #     product = await product_service.create(product_data)
    #
    #     assert product.url == product_data.url
    #     assert product.title == product_data.title
    #     assert product.current_price == product_data.current_price
    #     mock_session.add.assert_called_once()
    #     mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_products_by_store(self, product_service, mock_session):
        """Test getting products by store."""
        external_id = "test-123"
        store_name = "test_store"

        mock_products = [
            Product(id=1, url="url1", title="Product 1", external_id=external_id, store_name=store_name),
            Product(id=2, url="url2", title="Product 2", external_id=external_id, store_name=store_name),
        ]

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_products
        mock_session.execute.return_value = mock_result

        products = await product_service.get_by_external_id(external_id, store_name)

        assert products is not None
        assert len(products) == 2
        assert all(p.store_name == store_name for p in products)

    @pytest.mark.asyncio
    async def test_search_products(self, product_service, mock_session):
        """Test product search."""
        query = "test query"

        mock_products = [
            Product(id=1, url="url1", title="Test Product", brand="Test Brand"),
        ]

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_products
        mock_session.execute.return_value = mock_result

        products = await product_service.search(query)

        assert len(products) == 1
        assert "test" in products[0].title.lower()
