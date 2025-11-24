# backend/app/scrapers/demo.py

from decimal import Decimal
from pathlib import Path
from urllib.parse import urlparse

from app.scrapers.base import BaseScraper, ScrapedProduct, logger


class DemoScraper(BaseScraper):
    """Demo scraper for testing and examples."""

    def __init__(self):
        super().__init__("demo")

    def can_handle_url(self, url: str) -> bool:
        return "demo.com" in url.strip().lower()

    async def scrape_product(self, url: str) -> ScrapedProduct:
        # validate URL
        url = url.strip().lower()
        parsed = urlparse(url)

        print(f"\n\n parsed: {parsed}")
        print(f"\n\n hostname: {parsed.hostname}")

        if not parsed.hostname:
            raise ValueError("Invalid URL: hostname is required")
        if not parsed.path:
            raise ValueError("Invalid URL: path is required")

        examples_dir = Path(__file__).parent.parent.parent.parent / "examples"
        file_name = parsed.path.strip("/")  # get filename from url
        file_path = examples_dir / file_name
        print(f"\n\n filepath: {file_path}")
        if not file_path.exists():
            logger.warning(f"Demo HTML file not found: {file_path}. Falling back to default product page.")
            file_path = examples_dir / "sample_product_page.html"

        with open(file_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        soup = self.get_soup(html_content)

        title_elem = soup.find("h1", class_="product-title") or soup.find("h1")
        title = self.extract_text(title_elem) if title_elem else "Demo Product"

        price_elem = soup.find(class_=["price", "product-price"]) or soup.find("span",
                                                                               string=lambda text: text and "$" in text)
        price, currency = self.parse_price(self.extract_text(price_elem)) if price_elem else (Decimal("99.99"), "USD")

        brand_elem = soup.find(class_=["brand", "product-brand"])
        brand = self.extract_text(brand_elem) if brand_elem else "Unknown Brand"

        image_elem = soup.find("img", class_=["product-image", "main-image"]) or soup.find("img")
        image_url = image_elem.get("src") if image_elem else None

        # Use SKU as or file name as external_id
        sku_elem = soup.find(string=lambda text: text and "SKU:" in text)
        sku = sku_elem.strip().split(": ")[1] if sku_elem else f"demo-{file_name}"

        return ScrapedProduct(
            title=title,
            price=price,
            currency=currency,
            brand=brand,
            image_url=image_url,
            external_id=sku,
        )
