# tests/test_scrapers.py

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, Mock, patch

from app.scrapers.base import BaseScraper, ScrapedProduct
from app.scrapers.demo import DemoScraper
from app.scrapers.webscraper_io import WebScraperIOScraper
from app.scrapers.ebay import EbayScraper
from app.scrapers.etsy import EtsyScraper
from app.scrapers import get_scraper_for_url


class TestBaseScraper:
    """Test base scraper functionality."""
    
    def test_parse_price_usd(self):
        """Test parsing USD prices."""
        scraper = DemoScraper()
        
        # Test various price formats
        price, currency = scraper.parse_price("$99.99")
        assert price == Decimal("99.99")
        assert currency == "USD"
        
        price, currency = scraper.parse_price("$1,299.00")
        assert price == Decimal("1299.00")
        assert currency == "USD"
        
        price, currency = scraper.parse_price("Price: $49")
        assert price == Decimal("49")
        assert currency == "USD"
    
    def test_parse_price_other_currencies(self):
        """Test parsing other currencies."""
        scraper = DemoScraper()
        
        price, currency = scraper.parse_price("€79.99")
        assert price == Decimal("79.99")
        assert currency == "EUR"
        
        price, currency = scraper.parse_price("£49.50")
        assert price == Decimal("49.50")
        assert currency == "GBP"
    
    def test_parse_price_invalid(self):
        """Test parsing invalid price strings."""
        scraper = DemoScraper()
        
        price, currency = scraper.parse_price("")
        assert price is None
        assert currency == "USD"
        
        price, currency = scraper.parse_price("Out of stock")
        assert price is None
        assert currency == "USD"
    
    @pytest.mark.asyncio
    async def test_check_robots_txt(self):
        """Test robots.txt checking."""
        scraper = DemoScraper()
        
        with patch.object(scraper.client, 'get') as mock_get:
            # Mock robots.txt response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = "User-agent: *\nDisallow: /admin"
            mock_get.return_value = mock_response
            
            # Should allow scraping of non-admin pages
            allowed = await scraper.check_robots_txt("https://example.com/product")
            assert allowed is True


class TestDemoScraper:
    """Test demo scraper."""
    
    def test_can_handle_url(self):
        """Test URL handling."""
        scraper = DemoScraper()
        
        assert scraper.can_handle_url("demo://product/123")
        assert scraper.can_handle_url("https://demo.example.com/product")
        assert not scraper.can_handle_url("https://ebay.com/item/123")
    
    @pytest.mark.asyncio
    async def test_scrape_product(self, sample_scraped_data):
        """Test scraping demo product."""
        scraper = DemoScraper()
        
        # The demo scraper reads from a local HTML file
        try:
            result = await scraper.scrape_product("demo://product/123")
            assert isinstance(result, ScrapedProduct)
            assert result.title
            assert result.external_id == "demo-123"
        except FileNotFoundError:
            # If sample HTML file doesn't exist in test environment, that's OK
            pytest.skip("Sample HTML file not found")


class TestWebScraperIOScraper:
    """Test WebScraper.io scraper."""
    
    def test_can_handle_url(self):
        """Test URL handling."""
        scraper = WebScraperIOScraper()
        
        assert scraper.can_handle_url("https://webscraper.io/test-sites/e-commerce")
        assert not scraper.can_handle_url("https://ebay.com/item/123")
    
    @pytest.mark.asyncio
    async def test_scrape_product_mock(self):
        """Test scraping with mocked response."""
        scraper = WebScraperIOScraper()
        
        mock_html = """
        <html>
            <body>
                <h1>Test Product</h1>
                <div class="price">$29.99</div>
                <div class="brand">Test Brand</div>
                <img src="/test-image.jpg" class="product-image">
            </body>
        </html>
        """
        
        with patch.object(scraper, 'make_request') as mock_request:
            mock_response = Mock()
            mock_response.text = mock_html
            mock_request.return_value = mock_response
            
            with patch.object(scraper, 'check_robots_txt', return_value=True):
                result = await scraper.scrape_product("https://webscraper.io/test")
                
                assert result.title == "Test Product"
                assert result.price == Decimal("29.99")
                assert result.currency == "USD"
                assert result.brand == "Test Brand"


class TestEbayScraper:
    """Test eBay scraper."""
    
    def test_can_handle_url(self):
        """Test URL handling."""
        scraper = EbayScraper()
        
        assert scraper.can_handle_url("https://www.ebay.com/itm/123456789")
        assert scraper.can_handle_url("https://ebay.co.uk/itm/product-name/123456789")
        assert not scraper.can_handle_url("https://amazon.com/dp/B123")
    
    def test_extract_item_id(self):
        """Test extracting eBay item ID from URLs."""
        scraper = EbayScraper()
        
        # Standard format
        item_id = scraper.extract_item_id("https://www.ebay.com/itm/123456789")
        assert item_id == "123456789"
        
        # With product name
        item_id = scraper.extract_item_id("https://www.ebay.com/itm/product-name/123456789")
        assert item_id == "123456789"
        
        # Invalid URL
        item_id = scraper.extract_item_id("https://www.ebay.com/invalid")
        assert item_id is None
    
    @pytest.mark.asyncio
    async def test_scrape_product_mock(self, mock_ebay_response):
        """Test scraping with mocked eBay API response."""
        scraper = EbayScraper()
        
        with patch.object(scraper, 'get_access_token', return_value="fake_token"):
            with patch.object(scraper, 'make_request_with_rate_limit') as mock_request:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = mock_ebay_response
                mock_request.return_value = mock_response
                
                result = await scraper.scrape_product("https://www.ebay.com/itm/123456789")
                
                assert result.title == "iPhone 14 Pro Max"
                assert result.price == Decimal("999.99")
                assert result.currency == "USD"
                assert result.brand == "Apple"


class TestEtsyScraper:
    """Test Etsy scraper."""
    
    def test_can_handle_url(self):
        """Test URL handling."""
        scraper = EtsyScraper()
        
        assert scraper.can_handle_url("https://www.etsy.com/listing/123456789/product-name")
        assert not scraper.can_handle_url("https://ebay.com/item/123")
    
    def test_extract_listing_id(self):
        """Test extracting Etsy listing ID from URLs."""
        scraper = EtsyScraper()
        
        listing_id = scraper.extract_listing_id("https://www.etsy.com/listing/123456789/product-name")
        assert listing_id == "123456789"
        
        # Invalid URL
        listing_id = scraper.extract_listing_id("https://www.etsy.com/invalid")
        assert listing_id is None
    
    @pytest.mark.asyncio
    async def test_scrape_product_mock(self, mock_etsy_response):
        """Test scraping with mocked Etsy API response."""
        scraper = EtsyScraper()
        
        with patch.object(scraper, 'make_request_with_rate_limit') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_etsy_response
            mock_request.return_value = mock_response
            
            result = await scraper.scrape_product("https://www.etsy.com/listing/123456789/necklace")
            
            assert result.title == "Handmade Necklace"
            assert result.price == Decimal("29.99")  # 2999 cents / 100
            assert result.currency == "USD"
            assert result.brand == "HandmadeJewelry"


class TestScraperRegistry:
    """Test scraper registry functionality."""
    
    def test_get_scraper_for_url(self):
        """Test getting appropriate scraper for URL."""
        # eBay URL
        scraper = get_scraper_for_url("https://www.ebay.com/itm/123456789")
        assert isinstance(scraper, EbayScraper)
        
        # Etsy URL
        scraper = get_scraper_for_url("https://www.etsy.com/listing/123456789")
        assert isinstance(scraper, EtsyScraper)
        
        # Demo URL
        scraper = get_scraper_for_url("demo://product/123")
        assert isinstance(scraper, DemoScraper)
        
        # WebScraper.io URL
        scraper = get_scraper_for_url("https://webscraper.io/test-sites")
        assert isinstance(scraper, WebScraperIOScraper)
    
    def test_get_scraper_for_unsupported_url(self):
        """Test handling unsupported URLs."""
        with pytest.raises(ValueError, match="No scraper found"):
            get_scraper_for_url("https://unsupported-site.com/product/123")
