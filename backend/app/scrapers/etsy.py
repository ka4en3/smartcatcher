# backend/app/scrapers/etsy.py

import logging
from decimal import Decimal
from typing import Optional
from urllib.parse import urlparse

import httpx

from app.config import get_settings
from app.scrapers.base import BaseScraper, ScrapedProduct

settings = get_settings()
logger = logging.getLogger(__name__)


class EtsyScraper(BaseScraper):
    """Etsy API scraper using official Open API v3."""

    def __init__(self):
        super().__init__("etsy")

    def can_handle_url(self, url: str) -> bool:
        """Check if this is an Etsy URL."""
        return "etsy.com" in url

    def extract_listing_id(self, url: str) -> Optional[str]:
        """Extract Etsy listing ID from URL."""
        # Etsy URLs format: https://www.etsy.com/listing/123456789/product-name
        parsed = urlparse(url)
        path_parts = parsed.path.strip("/").split("/")

        if len(path_parts) >= 2 and path_parts[0] == "listing":
            listing_id = path_parts[1]
            if listing_id.isdigit():
                return listing_id

        return None

    async def scrape_product(self, url: str) -> ScrapedProduct:
        """Scrape product using Etsy Open API v3."""
        listing_id = self.extract_listing_id(url)
        if not listing_id:
            raise ValueError(f"Could not extract listing ID from Etsy URL: {url}")

        # Make API request
        api_url = f"{settings.etsy_base_url}/application/listings/{listing_id}"
        headers = {
            "x-api-key": settings.etsy_api_key,
            "Content-Type": "application/json",
        }

        # Add includes for additional data
        params = {
            "includes": "Images,Shop"
        }

        response = await self.make_request_with_rate_limit(api_url, headers=headers, params=params)

        if response.status_code == 404:
            raise ValueError(f"Etsy listing not found: {listing_id}")

        response.raise_for_status()
        listing_data = response.json()

        # Parse response data
        title = listing_data.get("title", "Unknown Product")

        # Extract price
        price = None
        currency = "USD"
        if "price" in listing_data:
            price_info = listing_data["price"]
            if "amount" in price_info:
                try:
                    # Etsy returns price in minor units (cents)
                    price_amount = price_info["amount"]
                    divisor = price_info.get("divisor", 100)
                    price = Decimal(str(price_amount)) / Decimal(str(divisor))
                    currency = price_info.get("currency_code", "USD")
                except (ValueError, TypeError, KeyError):
                    pass

        # Extract brand/shop name
        brand = None
        if "shop" in listing_data:
            brand = listing_data["shop"].get("shop_name")

        # Extract image URL
        image_url = None
        if "images" in listing_data and listing_data["images"]:
            # Get the first image
            first_image = listing_data["images"][0]
            image_url = first_image.get("url_570xN")  # Medium size image
            if not image_url:
                image_url = first_image.get("url_fullxfull")  # Full size fallback

        # Extract description (first 200 chars)
        description = None
        if "description" in listing_data:
            desc_text = listing_data["description"]
            if desc_text:
                description = desc_text[:200] + "..." if len(desc_text) > 200 else desc_text

        return ScrapedProduct(
            title=title,
            price=price,
            currency=currency,
            brand=brand,
            image_url=image_url,
            description=description,
            external_id=listing_id,
        )

    async def make_request_with_rate_limit(self, url: str, **kwargs) -> httpx.Response:
        """Make request with Etsy-specific rate limiting."""
        import asyncio

        # Etsy has 10 requests per second limit
        # Add a small delay to be safe
        await asyncio.sleep(0.11)  # ~9 requests per second

        response = await self.make_request(url, **kwargs)

        # Log rate limit headers
        if "X-RateLimit-Remaining" in response.headers:
            remaining = response.headers["X-RateLimit-Remaining"]
            reset_time = response.headers.get("X-RateLimit-Reset")
            logger.info(f"Etsy API rate limit remaining: {remaining}, resets at: {reset_time}")

        # Handle rate limiting
        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After", "60")
            logger.warning(f"Etsy rate limit exceeded, waiting {retry_after} seconds")
            await asyncio.sleep(int(retry_after))
            # Retry the request
            return await self.make_request(url, **kwargs)

        return response
