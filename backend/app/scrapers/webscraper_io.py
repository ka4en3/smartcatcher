# backend/app/scrapers/webscraper_io.py

from decimal import Decimal
from typing import Optional

from app.scrapers.base import BaseScraper, ScrapedProduct, logger


class WebScraperIOScraper(BaseScraper):
    """Scraper for webscraper.io test sites."""

    def __init__(self):
        super().__init__("webscraper_io")

    def can_handle_url(self, url: str) -> bool:
        """Check if this is a webscraper.io URL."""
        return "webscraper.io" in url

    async def scrape_product(self, url: str) -> ScrapedProduct:
        """Scrape product from webscraper.io test site."""
        # Check robots.txt (webscraper.io is designed for scraping practice)
        robots_allowed = await self.check_robots_txt(url)
        if not robots_allowed:
            logger.warning(f"Scraping not allowed by robots.txt for {url}")
            # raise ValueError(f"Scraping not allowed by robots.txt for {url}")  # webscraper.io is designed for scraping practice

        response = await self.make_request(url)
        soup = self.get_soup(response.text)

        # Parse product details based on webscraper.io structure
        # The site has different layouts, so we try multiple selectors

        # Try to find product title
        title_selectors = [
            "h1",
            ".product-title",
            ".title",
            "h2",
            ".name"
        ]

        title = None
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                title = self.extract_text(title_elem)
                if title:
                    break

        if not title:
            title = "Unknown Product"

        # Try to find price
        price_selectors = [
            ".price",
            ".product-price",
            "[class*='price']",
            ".cost",
            ".amount"
        ]

        price = None
        currency = "USD"
        for selector in price_selectors:
            price_elem = soup.select_one(selector)
            if price_elem:
                price_text = self.extract_text(price_elem)
                if price_text and any(char.isdigit() for char in price_text):
                    price, currency = self.parse_price(price_text)
                    if price:
                        break

        # Try to find brand
        brand_selectors = [
            ".brand",
            ".manufacturer",
            "[class*='brand']"
        ]

        brand = None
        for selector in brand_selectors:
            brand_elem = soup.select_one(selector)
            if brand_elem:
                brand = self.extract_text(brand_elem)
                if brand:
                    break

        # Try to find image
        image_selectors = [
            ".product-image img",
            ".image img",
            "img[src*='product']",
            ".product img",
            "img"
        ]

        image_url = None
        for selector in image_selectors:
            image_elem = soup.select_one(selector)
            if image_elem and image_elem.get("src"):
                image_url = image_elem.get("src")
                # Make absolute URL if relative
                if image_url and not image_url.startswith(("http", "https")):
                    from urllib.parse import urljoin
                    image_url = urljoin(url, image_url)
                break

        return ScrapedProduct(
            title=title,
            price=price,
            currency=currency,
            brand=brand,
            image_url=image_url,
            external_id=url.split("/")[-1] if "/" in url else None,
        )
