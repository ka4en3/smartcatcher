# tests/test_scrapers.py

import pytest
from decimal import Decimal
import respx
from httpx import Response

from app.scrapers import get_scraper_for_url
from app.scrapers.base import BaseScraper
from app.scrapers.demo import DemoScraper
from app.scrapers.ebay import EbayScraper
from app.scrapers.etsy import EtsyScraper
from app.scrapers.webscraper_io import WebScraperIOScraper
from app.config import Settings

# Use pytest-asyncio for all async tests in this module
pytestmark = pytest.mark.asyncio


# --- Test Scraper Registry ---

class TestScraperRegistry:
    """Tests for the scraper factory function get_scraper_for_url."""

    @pytest.mark.parametrize(
        "url, expected_scraper_class",
        [
            ("demo://product-1", DemoScraper),
            ("https://www.webscraper.io/test-sites/e-commerce/allinone/product/549", WebScraperIOScraper),
            ("https://www.ebay.com/itm/1234567890", EbayScraper),
            ("https://www.etsy.com/listing/123456789/cool-product-name", EtsyScraper),
        ],
    )
    def test_get_scraper_for_url_success(self, url, expected_scraper_class):
        """Test that the correct scraper is returned for a given URL."""
        scraper = get_scraper_for_url(url)
        assert isinstance(scraper, expected_scraper_class)

    def test_get_scraper_for_url_not_found(self):
        """Test that a ValueError is raised for an unsupported URL."""
        with pytest.raises(ValueError, match="No scraper found for URL"):
            get_scraper_for_url("https://www.unsupported-store.com/product")


# --- Test BaseScraper Utilities ---

class TestBaseScraper:
    """Tests for utility methods in the BaseScraper class."""

    @pytest.fixture
    def base_scraper(self) -> BaseScraper:
        """Fixture for a concrete instance of BaseScraper for testing."""

        class ConcreteScraper(BaseScraper):
            def can_handle_url(self, url): return True

            async def scrape_product(self, url): pass

        return ConcreteScraper("test_base")

    @pytest.mark.parametrize(
        "price_text, expected_price, expected_currency",
        [
            ("$149.99", Decimal("149.99"), "USD"),
            ("Price: €50.00", Decimal("50.00"), "EUR"),
            ("£25", Decimal("25"), "GBP"),
            ("Just 999 ₽", Decimal("999"), "RUB"),
            ("1,234.56", Decimal("1234.56"), "USD"),
            ("No price here", None, "USD"),
            ("", None, "USD"),
        ],
    )
    def test_parse_price(self, base_scraper, price_text, expected_price, expected_currency):
        """Test the price parsing logic with various formats."""
        price, currency = base_scraper.parse_price(price_text)
        assert price == expected_price
        assert currency == expected_currency


# --- Test Concrete Scrapers ---

class TestDemoScraper:
    """Tests for the DemoScraper."""

    @pytest.fixture
    def scraper(self) -> DemoScraper:
        return DemoScraper()

    async def test_scrape_product_success(self, scraper, mocker):
        """Test successful scraping from the local demo HTML file."""
        # This HTML content matches the `examples/sample_product_page.html` file
        html_content = """
        <!DOCTYPE html>
        <html>
        <body>
            <h1 class="product-title">Smart Fitness Watch Pro</h1>
            <div class="product-brand brand">TechGear</div>
            <div class="product-price price">$149.99</div>
            <img src="https://via.placeholder.com/300" class="product-image main-image">
        </body>
        </html>
        """
        # Mock the file system read operation
        mocker.patch("builtins.open", mocker.mock_open(read_data=html_content))
        mocker.patch("pathlib.Path.exists", return_value=True)

        product = await scraper.scrape_product("demo://test")

        assert product.title == "Smart Fitness Watch Pro"
        assert product.price == Decimal("149.99")
        assert product.currency == "USD"
        assert product.brand == "TechGear"
        assert product.image_url == "https://via.placeholder.com/300"
        assert product.external_id == "demo-123"

    async def test_scrape_product_file_not_found(self, scraper, mocker):
        """Test that an error is raised if the demo file is not found."""
        mocker.patch("pathlib.Path.exists", return_value=False)
        with pytest.raises(ValueError, match="Demo HTML file not found"):
            await scraper.scrape_product("demo://test")


class TestWebScraperIOScraper:
    """Tests for the WebScraperIOScraper."""

    @pytest.fixture
    def scraper(self) -> WebScraperIOScraper:
        return WebScraperIOScraper()

    @respx.mock
    async def test_scrape_product_success(self, scraper):
        """Test successful scraping of a webscraper.io page."""
        test_url = "https://www.webscraper.io/test-sites/e-commerce/allinone/product/549"

        # Mock HTML content for the test page
        html_content = """
        <html>
        <body>
            <div class="caption">
                <h4 class="price">$1016.99</h4>
                <h4><a href="/test-sites/e-commerce/allinone/product/549" class="title">Asus LT2000</a></h4>
                <p class="description">Description of Asus LT2000</p>
            </div>
            <img class="img-responsive" src="/images/test-sites/e-commerce/items/cart2.png">
        </body>
        </html>
        """
        # Mock the HTTP GET request
        respx.get(test_url).mock(return_value=Response(200, text=html_content))
        # Mock robots.txt check to always allow
        respx.get("https://www.webscraper.io/robots.txt").mock(return_value=Response(404))

        product = await scraper.scrape_product(test_url)

        assert product.title == "Asus LT2000"
        assert product.price == Decimal("1016.99")
        assert product.currency == "USD"
        assert product.image_url == "https://www.webscraper.io/images/test-sites/e-commerce/items/cart2.png"
        assert product.external_id == "549"


class TestEbayScraper:
    """Tests for the EbayScraper."""
    @pytest.fixture
    def settings(self):
        return Settings()

    @pytest.fixture
    def scraper(self) -> EbayScraper:
        return EbayScraper()

    @pytest.mark.parametrize("url, expected_id", [
        ("https://www.ebay.com/itm/123456789012", "123456789012"),
        ("https://www.ebay.com/itm/Some-Product-Title-Here/210987654321", "210987654321"),
        ("https://www.ebay.de/p/987654321", "987654321"),
        ("https://www.ebay.co.uk/itm/123?item=555444333", "555444333"),
        ("https://www.ebay.com/some/other/path", None)
    ])
    def test_extract_item_id(self, scraper, url, expected_id):
        """Test extraction of item ID from various eBay URL formats."""
        assert scraper.extract_item_id(url) == expected_id

    @respx.mock
    async def test_scrape_product_success(self, scraper, settings):
        """Test successful scraping via mocked eBay API."""
        item_id = "1234567890"
        test_url = f"https://www.ebay.com/itm/{item_id}"

        # Mock eBay OAuth2 token request
        respx.post(f"{settings.ebay_base_url}/identity/v1/oauth2/token").mock(
            return_value=Response(200, json={"access_token": "fake_token", "expires_in": 7200})
        )

        # Mock eBay Browse API response
        api_response_json = {
            "itemId": f"v1|{item_id}|0",
            "title": "Test eBay Product",
            "price": {"value": "199.99", "currency": "USD"},
            "image": {"imageUrl": "https://i.ebayimg.com/images/g/test.jpg"},
            "localizedAspects": [{"name": "Brand", "value": "TestBrand"}]
        }
        respx.get(f"{settings.ebay_base_url}/buy/browse/v1/item/{item_id}").mock(
            return_value=Response(200, json=api_response_json)
        )

        product = await scraper.scrape_product(test_url)

        assert product.title == "Test eBay Product"
        assert product.price == Decimal("199.99")
        assert product.currency == "USD"
        assert product.brand == "TestBrand"
        assert product.image_url == "https://i.ebayimg.com/images/g/test.jpg"
        assert product.external_id == item_id


class TestEtsyScraper:
    """Tests for the EtsyScraper."""
    @pytest.fixture
    def settings(self):
        return Settings()

    @pytest.fixture
    def scraper(self) -> EtsyScraper:
        return EtsyScraper()

    @pytest.mark.parametrize("url, expected_id", [
        ("https://www.etsy.com/listing/123456789/my-awesome-product", "123456789"),
        ("https://www.etsy.com/de/listing/987654321/another-product-title", "987654321"),
        ("https://www.etsy.com/c/some-category/listing", None)
    ])
    def test_extract_listing_id(self, scraper, url, expected_id):
        """Test extraction of listing ID from various Etsy URL formats."""
        assert scraper.extract_listing_id(url) == expected_id

    @respx.mock
    async def test_scrape_product_success(self, scraper, settings):
        """Test successful scraping via mocked Etsy API."""
        listing_id = "123456789"
        test_url = f"https://www.etsy.com/listing/{listing_id}/test-product"

        # Mock Etsy API v3 response
        api_response_json = {
            "listing_id": int(listing_id),
            "title": "Handmade Test Product",
            "description": "A very nice product for testing purposes.",
            "price": {"amount": 2550, "divisor": 100, "currency_code": "EUR"},
            "shop": {"shop_name": "CraftyTesters"},
            "images": [{"url_570xN": "https://i.etsystatic.com/test_image.jpg"}]
        }
        api_url = f"{settings.etsy_base_url}/application/listings/{listing_id}"
        respx.get(url__regex=f"^{api_url}.*").mock(
            return_value=Response(200, json=api_response_json)
        )

        product = await scraper.scrape_product(test_url)

        assert product.title == "Handmade Test Product"
        # Etsy price is amount / divisor
        assert product.price == Decimal("25.50")
        assert product.currency == "EUR"
        assert product.brand == "CraftyTesters"
        assert product.image_url == "https://i.etsystatic.com/test_image.jpg"
        assert product.description.startswith("A very nice product")
        assert product.external_id == listing_id