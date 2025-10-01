"""Unit tests for scraper components."""
import pytest
from unittest.mock import Mock, patch
from decimal import Decimal

from app.scrapers.base import BaseProductScraper, ScrapedProduct
from app.scrapers.amazon import AmazonScraper
from app.scrapers.ebay import EbayScraper


class TestBaseProductScraper:
    """Test base scraper functionality."""

    def test_scraped_product_creation(self):
        """Test ScrapedProduct model creation."""
        product = ScrapedProduct(
            title="Test Product",
            price=Decimal("29.99"),
            currency="USD",
            brand="Test Brand",
            image_url="https://example.com/image.jpg",
            external_id="test-123"
        )

        assert product.title == "Test Product"
        assert product.price == Decimal("29.99")
        assert product.currency == "USD"
        assert product.brand == "Test Brand"

    def test_scraped_product_validation(self):
        """Test ScrapedProduct validation."""
        # Valid product
        valid_product = ScrapedProduct(
            title="Valid Product",
            price=Decimal("19.99"),
            currency="EUR"
        )
        assert valid_product.title == "Valid Product"

        # Invalid price should raise validation error
        with pytest.raises(ValueError):
            ScrapedProduct(
                title="Invalid Product",
                price=Decimal("-10.00"),  # Negative price
                currency="USD"
            )


class TestAmazonScraper:
    """Test Amazon scraper."""

    @pytest.fixture
    def amazon_scraper(self):
        """Create Amazon scraper instance."""
        return AmazonScraper()

    def test_extract_asin_from_url(self, amazon_scraper):
        """Test ASIN extraction from Amazon URLs."""
        test_cases = [
            ("https://www.amazon.com/dp/B08N5WRWNW", "B08N5WRWNW"),
            ("https://amazon.com/gp/product/B08N5WRWNW", "B08N5WRWNW"),
            ("https://www.amazon.de/dp/B08N5WRWNW/ref=sr_1_1", "B08N5WRWNW"),
        ]

        for url, expected_asin in test_cases:
            asin = amazon_scraper.extract_asin(url)
            assert asin == expected_asin

    def test_extract_asin_invalid_url(self, amazon_scraper):
        """Test ASIN extraction from invalid URLs."""
        invalid_urls = [
            "https://not-amazon.com/product/123",
            "https://amazon.com/invalid",
            "not-a-url-at-all"
        ]

        for url in invalid_urls:
            asin = amazon_scraper.extract_asin(url)
            assert asin is None

    @patch('httpx.AsyncClient.get')
    @pytest.mark.asyncio
    async def test_scrape_product_success(self, mock_get, amazon_scraper):
        """Test successful product scraping."""
        # Mock successful HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
            <head><title>Test Product</title></head>
            <body>
                <span class="a-price-whole">29</span>
                <span class="a-price-fraction">99</span>
                <span id="productTitle">Test Amazon Product</span>
                <div data-brand="TestBrand">Brand</div>
            </body>
        </html>
        """
        mock_get.return_value = mock_response

        url = "https://www.amazon.com/dp/B08N5WRWNW"
        product = await amazon_scraper.scrape_product(url)

        assert product is not None
        assert "Test" in product.title
        assert product.external_id == "B08N5WRWNW"

    @patch('httpx.AsyncClient.get')
    @pytest.mark.asyncio
    async def test_scrape_product_failure(self, mock_get, amazon_scraper):
        """Test failed product scraping."""
        # Mock failed HTTP response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        url = "https://www.amazon.com/dp/INVALID"
        product = await amazon_scraper.scrape_product(url)

        assert product is None


class TestEbayScraper:
    """Test eBay scraper."""

    @pytest.fixture
    def ebay_scraper(self):
        return EbayScraper()

    def test_extract_item_id_from_url(self, ebay_scraper):
        """Test item ID extraction from eBay URLs."""
        test_cases = [
            ("https://www.ebay.com/itm/123456789012", "123456789012"),
            ("https://ebay.com/itm/987654321098?hash=item", "987654321098"),
            ("https://www.ebay.de/itm/111111111111/", "111111111111"),
        ]

        for url, expected_id in test_cases:
            item_id = ebay_scraper.extract_item_id(url)
            assert item_id == expected_id

    @patch('httpx.AsyncClient.get')
    @pytest.mark.asyncio
    async def test_scrape_product_with_api(self, mock_get, ebay_scraper):
        """Test product scraping using eBay API."""
        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "title": "Test eBay Product",
            "price": {"value": "45.99", "currency": "USD"},
            "brand": "eBayBrand",
            "image": {"imageUrl": "https://example.com/image.jpg"}
        }
        mock_get.return_value = mock_response

        url = "https://www.ebay.com/itm/123456789012"
        product = await ebay_scraper.scrape_product(url)

        assert product is not None
        assert product.title == "Test eBay Product"
        assert product.price == Decimal("45.99")
        assert product.currency == "USD"
