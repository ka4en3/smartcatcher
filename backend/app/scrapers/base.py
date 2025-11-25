# backend/app/scrapers/base.py

import logging
import sys
import asyncio

from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional
from urllib.robotparser import RobotFileParser

import httpx
from bs4 import BeautifulSoup

from app.config import get_settings

settings = get_settings()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


@dataclass
class ScrapedProduct:
    """Scraped product data."""

    title: str
    price: Optional[Decimal]
    currency: str
    image_url: Optional[str] = None
    brand: Optional[str] = None
    availability: Optional[str] = None
    description: Optional[str] = None
    external_id: Optional[str] = None


class BaseScraper(ABC):
    """Base scraper class."""

    def __init__(self, name: str):
        self.name = name
        self._client = None
        self._client_managed = False

    def _ensure_client(self):
        """Ensure HTTP client exists (lazy initialization)."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                headers={
                    "User-Agent": settings.scraper_user_agent,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                    "Accept-Encoding": "gzip, deflate",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1",
                },
                timeout=settings.scraper_timeout,
                follow_redirects=True,
            )
            self._client_managed = False  # Not managed by context manager

    @property
    def client(self):
        """Get HTTP client (creates if needed)."""
        self._ensure_client()
        return self._client

    async def __aenter__(self):
        """Async context manager entry."""
        self._ensure_client()
        self._client_managed = True
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._client is not None and self._client_managed:
            await self._client.aclose()
            self._client = None
            self._client_managed = False

    @abstractmethod
    def can_handle_url(self, url: str) -> bool:
        """Check if this scraper can handle the given URL."""
        pass

    @abstractmethod
    async def scrape_product(self, url: str) -> ScrapedProduct:
        """Scrape product data from URL."""
        pass

    async def check_robots_txt(self, url: str) -> bool:
        """Check if scraping is allowed by robots.txt."""
        try:
            from urllib.parse import urljoin, urlparse

            parsed_url = urlparse(url)
            robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"

            response = await self.client.get(robots_url)
            if response.status_code != 200:
                # If robots.txt doesn't exist, assume scraping is allowed
                return True

            rp = RobotFileParser()
            rp.set_url(robots_url)
            rp.read()

            user_agent = settings.scraper_user_agent
            return rp.can_fetch(user_agent, url)

        except Exception as e:
            logger.warning(f"Failed to check robots.txt for {url}: {e}")
            # If we can't check robots.txt, err on the side of caution
            return True

    async def make_request(self, url: str, **kwargs) -> httpx.Response:
        """Make HTTP request with retry logic and rate limiting."""
        last_exception = None

        for attempt in range(settings.scraper_retry_attempts):
            try:
                # Add delay between requests (respect rate limits)
                if attempt > 0:
                    delay = settings.scraper_request_delay * (2 ** (attempt - 1))  # Exponential backoff
                    await asyncio.sleep(delay)
                elif settings.scraper_request_delay > 0:
                    await asyncio.sleep(settings.scraper_request_delay)

                response = await self.client.get(url, **kwargs)

                # Handle rate limiting
                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After")
                    if retry_after:
                        await asyncio.sleep(int(retry_after))
                        continue
                    else:
                        # Default backoff for rate limiting
                        await asyncio.sleep(60)
                        continue

                response.raise_for_status()
                return response

            except (httpx.RequestError, httpx.HTTPStatusError) as e:
                last_exception = e
                logger.warning(
                    f"Request attempt {attempt + 1} failed for {url}: {e}"
                )

                if attempt < settings.scraper_retry_attempts - 1:
                    continue

        # All attempts failed
        raise last_exception or Exception("All retry attempts failed")

    def parse_price(self, price_text: str) -> tuple[Optional[Decimal], str]:
        """Parse price from text and extract currency."""
        if not price_text:
            return None, "USD"

        import re

        # Clean the price text
        price_text = price_text.strip().replace(",", "").replace("\n", " ")

        # Common currency symbols and their codes
        currency_map = {
            "$": "USD",
            "€": "EUR",
            "£": "GBP",
            "¥": "JPY",
            "₽": "RUB",
        }

        # Extract currency symbol
        currency = "USD"  # default
        for symbol, code in currency_map.items():
            if symbol in price_text:
                currency = code
                price_text = price_text.replace(symbol, "").strip()
                break

        # Extract numeric value
        price_match = re.search(r"(\d+\.?\d*)", price_text)
        if price_match:
            try:
                price = Decimal(price_match.group(1))
                return price, currency
            except (ValueError, TypeError):
                pass

        return None, currency

    def get_soup(self, html_content: str) -> BeautifulSoup:
        """Create BeautifulSoup object from HTML content."""
        return BeautifulSoup(html_content, "lxml")

    def extract_text(self, element) -> str:
        """Extract clean text from BeautifulSoup element."""
        if not element:
            return ""
        return element.get_text(strip=True)