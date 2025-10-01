# backend/app/scrapers/demo.py

import os
from decimal import Decimal
from pathlib import Path
from typing import Optional

from app.scrapers.base import BaseScraper, ScrapedProduct


class DemoScraper(BaseScraper):
    """Demo scraper for testing and examples."""

    def __init__(self):
        super().__init__("demo")

    def can_handle_url(self, url: str) -> bool:
        """Check if this is a demo URL."""
        return url.startswith("demo://") or "demo" in url.lower()

    async def scrape_product(self, url: str) -> ScrapedProduct:
        """Scrape demo product from local HTML file."""
        # Load sample HTML file
        examples_dir = Path(__file__).parent.parent.parent.parent / "examples"
        sample_file = examples_dir / "sample_product_page.html"
        
        if not sample_file.exists():
            raise ValueError(f"Demo HTML file not found: {sample_file}")
        
        with open(sample_file, "r", encoding="utf-8") as f:
            html_content = f.read()
        
        soup = self.get_soup(html_content)
        
        # Extract product information from demo HTML
        title_elem = soup.find("h1", class_="product-title") or soup.find("h1")
        title = self.extract_text(title_elem) if title_elem else "Demo Product"
        
        price_elem = soup.find(class_=["price", "product-price"]) or soup.find("span", string=lambda text: text and "$" in text)
        price, currency = self.parse_price(self.extract_text(price_elem)) if price_elem else (Decimal("99.99"), "USD")
        
        brand_elem = soup.find(class_=["brand", "product-brand"])
        brand = self.extract_text(brand_elem) if brand_elem else "Demo Brand"
        
        image_elem = soup.find("img", class_=["product-image", "main-image"]) or soup.find("img")
        image_url = image_elem.get("src") if image_elem else None
        
        return ScrapedProduct(
            title=title,
            price=price,
            currency=currency,
            brand=brand,
            image_url=image_url,
            external_id="demo-123",
        )
