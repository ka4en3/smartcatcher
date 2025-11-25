# backend/app/scrapers/demo.py

from pathlib import Path
from urllib.parse import urlparse

from app.scrapers.base import BaseScraper, ScrapedProduct, logger


class DemoScraper(BaseScraper):
    """Demo scraper that reuses WebScraperIO functionality via composition."""

    def __init__(self):
        super().__init__("demo")
        # Import here to avoid circular imports
        from app.scrapers.webscraper_io import WebScraperIOScraper
        self._webscraper_helper = WebScraperIOScraper()

    def can_handle_url(self, url: str) -> bool:
        """Check if this is a demo-server URL."""
        return "demo-server" in url.strip().lower()

    async def scrape_product(self, url: str) -> ScrapedProduct:
        """
        Scrape product from demo server using HTTP requests.
        Falls back to local HTML file if the page doesn't exist on the server.
        """
        url = url.strip()

        try:
            # Try to fetch from demo server using helper's HTTP functionality
            logger.info(f"Attempting to scrape demo server: {url}")
            response = await self._webscraper_helper.make_request(url)

            # If successful, parse the HTML
            soup = self._webscraper_helper.get_soup(response.text)

            # Extract product data
            return await self._parse_product_from_soup(soup, url)

        except Exception as e:
            # Fallback to local file
            logger.warning(
                f"Failed to fetch from demo server ({e}). "
                f"Falling back to local HTML file."
            )
            return await self._scrape_from_local_file(url)

    async def _parse_product_from_soup(self, soup, url: str) -> ScrapedProduct:
        """Parse product details from BeautifulSoup object."""

        # Extract title
        title_elem = (
                soup.find("h1", class_="product-title")
                or soup.find("h1")
        )
        title = self._webscraper_helper.extract_text(title_elem) if title_elem else "Demo Product"

        # Extract price
        price_elem = (
                soup.find(class_=["price", "product-price"])
                or soup.find("span", string=lambda text: text and "$" in text)
        )

        if price_elem:
            price_text = self._webscraper_helper.extract_text(price_elem)
            price, currency = self._webscraper_helper.parse_price(price_text)
        else:
            price, currency = None, "USD"

        # Extract brand
        brand_elem = soup.find(class_=["brand", "product-brand"])
        brand = self._webscraper_helper.extract_text(brand_elem) if brand_elem else None

        # Extract image
        image_elem = (
                soup.find("img", class_=["product-image", "main-image"])
                or soup.find("img")
        )
        image_url = image_elem.get("src") if image_elem else None

        # Make absolute URL if relative
        if image_url and not image_url.startswith(("http://", "https://")):
            from urllib.parse import urljoin
            image_url = urljoin(url, image_url)

        # Extract SKU as external_id
        # Look for hidden SKU or visible SKU text
        sku_elem = (
                soup.find("span", style=lambda s: s and "display:none" in s)
                or soup.find(string=lambda text: text and "SKU:" in str(text))
        )

        if sku_elem:
            sku_text = (
                self._webscraper_helper.extract_text(sku_elem)
                if hasattr(sku_elem, 'get_text')
                else str(sku_elem)
            )
            if "SKU:" in sku_text:
                external_id = sku_text.split("SKU:")[-1].strip()
            else:
                external_id = sku_text.strip()
        else:
            # Fallback: use last part of URL
            parsed = urlparse(url)
            filename = parsed.path.strip("/").replace(".html", "")
            external_id = f"demo-{filename}" if filename else "demo-unknown"

        return ScrapedProduct(
            title=title,
            price=price,
            currency=currency,
            brand=brand,
            image_url=image_url,
            external_id=external_id,
        )

    async def _scrape_from_local_file(self, url: str) -> ScrapedProduct:
        """Fallback: scrape from local HTML file."""
        parsed = urlparse(url)

        # Determine which local file to use
        examples_dir = Path(__file__).parent.parent.parent.parent / "examples"

        if parsed.path:
            file_name = parsed.path.strip("/")
            file_path = examples_dir / file_name
        else:
            file_path = None

        # If file doesn't exist, use fallback
        if not file_path or not file_path.exists():
            logger.warning(
                f"Demo HTML file not found: {file_path}. "
                f"Using sample_product_page.html"
            )
            file_path = examples_dir / "sample_product_page.html"

        if not file_path.exists():
            raise FileNotFoundError(
                f"Neither the requested file nor sample_product_page.html exist in {examples_dir}"
            )

        # Read local file
        with open(file_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        # Parse using helper's get_soup
        soup = self._webscraper_helper.get_soup(html_content)

        # Parse product data
        return await self._parse_product_from_soup(soup, url)