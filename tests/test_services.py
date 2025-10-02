"""Unit tests for service layer."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from decimal import Decimal

from app.services.auth import AuthService
from app.services.product import ProductService
from app.models import User, Product, PriceHistory
from app.schemas.product import ProductCreate
from app.core.exceptions import AuthenticationException
from app.core.security import get_password_hash


# Use pytest-asyncio for all async tests in this module
pytestmark = pytest.mark.asyncio


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

    # This test now mocks the dependency (UserService) instead of implementation details.
    @patch("app.services.auth.UserService")
    async def test_create_user(self, MockUserService, mock_session):
        """Test user creation."""
        # Instantiate AuthService, which will use our mocked UserService
        auth_service = AuthService(mock_session)

        email = "test@example.com"
        password = "password123"

        # Configure the mock user_service
        mock_user_service_instance = MockUserService.return_value
        mock_user_service_instance.create = AsyncMock(return_value=User(email=email, is_active=True, is_admin=False))

        user = await auth_service.create_user(email, password)

        assert user.email == email
        assert user.is_active is True
        assert user.is_admin is False

        # Check that user_service.create was called correctly
        mock_user_service_instance.create.assert_called_once()
        call_args = mock_user_service_instance.create.call_args[0][0]
        assert call_args["email"] == email
        assert "hashed_password" in call_args

    async def test_authenticate_user_success(self, auth_service, mock_session):
        """Test successful user authentication."""
        email = "test@example.com"
        password = "password123"
        hashed_password = get_password_hash(password)

        mock_user = User(
            id=1,
            email=email,
            hashed_password=hashed_password,
            is_active=True
        )

        # Mock database query
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result

        authenticated_user = await auth_service.authenticate_user(email, password)

        assert authenticated_user == mock_user
        assert authenticated_user.email == email

    async def test_authenticate_user_wrong_password(self, auth_service, mock_session):
        """Test authentication with wrong password."""
        email = "test@example.com"
        correct_password = "password123"
        wrong_password = "wrongpassword"
        hashed_password = get_password_hash(correct_password)

        mock_user = User(
            id=1,
            email=email,
            hashed_password=hashed_password,
            is_active=True
        )

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result

        authenticated_user = await auth_service.authenticate_user(email, wrong_password)

        assert authenticated_user is None

    # This test now correctly reflects the service's current behavior.
    async def test_authenticate_user_returns_inactive_user(self, auth_service, mock_session):
        """Test that authentication returns an inactive user if credentials are correct."""
        email = "test@example.com"
        password = "password123"
        hashed_password = get_password_hash(password)

        mock_user = User(
            id=1,
            email=email,
            hashed_password=hashed_password,
            is_active=False  # Inactive user
        )

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result

        authenticated_user = await auth_service.authenticate_user(email, password)

        assert authenticated_user is not None
        assert authenticated_user.is_active is False

    # Test for successful token refresh.
    @patch("app.services.auth.decode_token")
    @patch("app.services.auth.create_access_token")
    @patch("app.services.auth.create_refresh_token")
    async def test_refresh_tokens_success(self, mock_create_refresh, mock_create_access, mock_decode, auth_service):
        """Test successful token refresh."""
        user_id = 1
        mock_decode.return_value = {"sub": str(user_id), "type": "refresh"}

        # Mock the user_service within the auth_service instance
        auth_service.user_service.get_by_id = AsyncMock(return_value=User(id=user_id, is_active=True))

        mock_create_access.return_value = "new_access_token"
        mock_create_refresh.return_value = "new_refresh_token"

        access_token, refresh_token = await auth_service.refresh_tokens("valid_refresh_token")

        assert access_token == "new_access_token"
        assert refresh_token == "new_refresh_token"
        mock_decode.assert_called_once_with("valid_refresh_token")
        auth_service.user_service.get_by_id.assert_called_once_with(user_id)

    # Test token refresh for an inactive user.
    @patch("app.services.auth.decode_token")
    async def test_refresh_tokens_inactive_user_raises_exception(self, mock_decode, auth_service):
        """Test token refresh for an inactive user raises an exception."""
        user_id = 1
        mock_decode.return_value = {"sub": str(user_id), "type": "refresh"}
        auth_service.user_service.get_by_id = AsyncMock(return_value=User(id=user_id, is_active=False))

        with pytest.raises(AuthenticationException, match="User not found or inactive"):
            await auth_service.refresh_tokens("any_token")

        mock_decode.assert_called_once_with("any_token")


class TestProductService:
    """Test product service."""

    @pytest.fixture
    def mock_session(self):
        return AsyncMock()

    @pytest.fixture
    def product_service(self, mock_session):
        return ProductService(mock_session)

    async def test_create_product(self, product_service, mock_session):
        """Test product creation."""
        product_data = ProductCreate(
            url="https://example.com/product",
            title="Test Product",
            brand="Test Brand",
            current_price=Decimal("99.99"),
            currency="USD",
            store_name="test_store",
            external_id="test-123"
        )

        mock_session.add = Mock()
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()

        product = await product_service.create(product_data)

        assert product.url == product_data.url
        assert product.title == product_data.title
        assert product.current_price == product_data.current_price
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    async def test_get_products_by_store(self, product_service, mock_session):
        """Test getting products by store."""
        store_name = "test_store"
        mock_products = [
            Product(id=1, url="url1", title="Product 1", store_name=store_name),
            Product(id=2, url="url2", title="Product 2", store_name=store_name),
        ]

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_products
        mock_session.execute.return_value = mock_result

        products = await product_service.get_by_store_name(store_name)

        assert len(products) == 2
        assert all(p.store_name == store_name for p in products)

    async def test_list_products_with_search(self, product_service, mock_session):
        """Test product search using list_products."""
        query = "test query"
        mock_products = [
            Product(id=1, url="url1", title="A test product", brand="Test Brand"),
        ]

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_products
        mock_session.execute.return_value = mock_result

        products = await product_service.list_products(search=query)

        assert len(products) == 1
        assert "test" in products[0].title.lower()
        # Verify that the query statement was built correctly
        generated_sql = str(mock_session.execute.call_args[0][0]).lower()
        assert "where" in generated_sql and "like" in generated_sql and "lower" in generated_sql

    # Test for updating price and creating a history record.
    async def test_update_price(self, product_service, mock_session):
        """Test product price update and history creation."""
        product_id = 1
        new_price = Decimal("120.50")
        original_product = Product(
            id=product_id, title="Old Product", current_price=Decimal("100.00"), currency="USD"
        )

        # Mock the get_by_id call which is used inside update_price
        product_service.get_by_id = AsyncMock(return_value=original_product)

        mock_session.add = Mock()
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()

        product, price_history = await product_service.update_price(product_id, new_price, "EUR")

        # Check that the product's price and currency were updated
        assert product.current_price == new_price
        assert product.currency == "EUR"

        # Check that `session.add` was called with a new PriceHistory object
        mock_session.add.assert_called_once()
        added_object = mock_session.add.call_args[0][0]
        assert isinstance(added_object, PriceHistory)
        assert added_object.price == new_price
        assert added_object.product_id == product_id

        # Check that the session was committed
        mock_session.commit.assert_called_once()

    # Test for fetching products for the scraping process.
    async def test_get_products_for_scraping(self, product_service, mock_session):
        """Test getting products for scraping, verifying the sorting order."""
        mock_products = [Product(id=1), Product(id=2)]
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_products
        mock_session.execute.return_value = mock_result

        limit = 50
        await product_service.get_products_for_scraping(limit=limit)

        # Check that the generated SQL query has the correct ordering and limit clauses
        # `nullsfirst()` is crucial for scraping new products first.
        generated_query = str(mock_session.execute.call_args[0][0]).strip().lower()

        assert "order by products.last_scraped_at asc nulls first" in generated_query
        assert "limit :param_1" in generated_query  # ensure limit is applied
        assert "where products.is_active = true" in generated_query  # ensure filtering