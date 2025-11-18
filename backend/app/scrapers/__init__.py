# backend/app/scrapers/__init__.py

from .base import BaseScraper, ScrapedProduct
from .demo import DemoScraper
from .ebay import EbayScraper
from .etsy import EtsyScraper
from .webscraper_io import WebScraperIOScraper

# Registry of all available scrapers
SCRAPERS = [
    DemoScraper(),
    WebScraperIOScraper(),
    EbayScraper(),
    EtsyScraper(),
]


def get_scraper_for_url(url: str) -> BaseScraper:
    """Get appropriate scraper for URL."""
    for scraper in SCRAPERS:
        if scraper.can_handle_url(url):
            return scraper
    raise ValueError(f"No scraper found for URL: {url}")


__all__ = [
    "BaseScraper",
    "ScrapedProduct",
    "DemoScraper",
    "WebScraperIOScraper",
    "EbayScraper",
    "EtsyScraper",
    "SCRAPERS",
    "get_scraper_for_url",
]
