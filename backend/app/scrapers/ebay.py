# backend/app/scrapers/ebay.py

import json
import logging
from decimal import Decimal
from typing import Optional
from urllib.parse import parse_qs, urlparse

import httpx

from app.config import get_settings
from app.scrapers.base import BaseScraper, ScrapedProduct

settings = get_settings()
logger = logging.getLogger(__name__)


class EbayScraper(BaseScraper):
    """eBay API scraper using official Browse API."""

    def __init__(self):
        super().__init__("ebay")
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[int] = None

    def can_handle_url(self, url: str) -> bool:
        """Check if this is an eBay URL."""
        return "ebay.com" in url or "ebay." in url

    def extract_item_id(self, url: str) -> Optional[str]:
        """Extract eBay item ID from URL."""
        # eBay URLs can have various formats:
        # https://www.ebay.com/itm/123456789
        # https://www.ebay.com/itm/product-name/123456789
        # https://www.ebay.com/p/123456789
        
        parsed = urlparse(url)
        path_parts = parsed.path.strip("/").split("/")
        
        # Look for numeric item ID
        for part in path_parts:
            if part.isdigit() and len(part) >= 9:  # eBay item IDs are typically 9+ digits
                return part
        
        # Try query parameters
        query_params = parse_qs(parsed.query)
        if "item" in query_params:
            return query_params["item"][0]
        
        return None

    async def get_access_token(self) -> str:
        """Get OAuth access token for eBay API."""
        import time
        
        # Check if we have a valid token
        if self.access_token and self.token_expires_at and time.time() < self.token_expires_at:
            return self.access_token
        
        # Get new token
        token_url = f"{settings.ebay_base_url}/identity/v1/oauth2/token"
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {self._get_basic_auth_header()}",
        }
        
        data = {
            "grant_type": "client_credentials",
            "scope": "https://api.ebay.com/oauth/api_scope"
        }
        
        response = await self.client.post(token_url, headers=headers, data=data)
        response.raise_for_status()
        
        token_data = response.json()
        self.access_token = token_data["access_token"]
        # Set expiration time (subtract 5 minutes for safety)
        self.token_expires_at = time.time() + token_data["expires_in"] - 300
        
        return self.access_token

    def _get_basic_auth_header(self) -> str:
        """Generate basic auth header for OAuth."""
        import base64
        
        credentials = f"{settings.ebay_client_id}:{settings.ebay_client_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        return encoded_credentials

    async def scrape_product(self, url: str) -> ScrapedProduct:
        """Scrape product using eBay Browse API."""
        item_id = self.extract_item_id(url)
        if not item_id:
            raise ValueError(f"Could not extract item ID from eBay URL: {url}")
        
        access_token = await self.get_access_token()
        
        # Make API request
        api_url = f"{settings.ebay_base_url}/buy/browse/v1/item/{item_id}"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        
        response = await self.make_request_with_rate_limit(api_url, headers=headers)
        
        if response.status_code == 404:
            raise ValueError(f"eBay item not found: {item_id}")
        
        response.raise_for_status()
        item_data = response.json()
        
        # Parse response data
        title = item_data.get("title", "Unknown Product")
        
        # Extract price
        price = None
        currency = "USD"
        if "price" in item_data:
            price_info = item_data["price"]
            if "value" in price_info:
                try:
                    price = Decimal(str(price_info["value"]))
                    currency = price_info.get("currency", "USD")
                except (ValueError, TypeError):
                    pass
        
        # Extract brand (if available in item specifics)
        brand = None
        if "localizedAspects" in item_data:
            for aspect in item_data["localizedAspects"]:
                if aspect.get("name", "").lower() in ["brand", "marca", "marque"]:
                    brand = aspect.get("value")
                    break
        
        # Extract image URL
        image_url = None
        if "image" in item_data:
            image_url = item_data["image"].get("imageUrl")
        elif "additionalImages" in item_data and item_data["additionalImages"]:
            image_url = item_data["additionalImages"][0].get("imageUrl")
        
        return ScrapedProduct(
            title=title,
            price=price,
            currency=currency,
            brand=brand,
            image_url=image_url,
            external_id=item_id,
        )

    async def make_request_with_rate_limit(self, url: str, **kwargs) -> httpx.Response:
        """Make request with eBay-specific rate limiting."""
        response = await self.make_request(url, **kwargs)
        
        # Log rate limit headers
        if "X-RateLimit-Remaining" in response.headers:
            remaining = response.headers["X-RateLimit-Remaining"]
            logger.info(f"eBay API rate limit remaining: {remaining}")
            
            # If we're running low on requests, add extra delay
            if int(remaining) < 100:
                import asyncio
                await asyncio.sleep(2)
        
        return response
