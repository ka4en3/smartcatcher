# worker/tasks/scraper.py

import asyncio
import logging
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from celery import current_app
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

# Import backend components
from app.config import get_settings
from app.models.product import Product, PriceHistory
from app.models.subscription import Subscription, SubscriptionType
from app.scrapers import get_scraper_for_url
from app.services.notification import NotificationService
from app.services.product import ProductService
from app.services.subscription import SubscriptionService

settings = get_settings()
logger = logging.getLogger(__name__)

# Create async engine for worker
engine = create_async_engine(
    settings.database_url.replace("postgresql://", "postgresql+asyncpg://"),
    echo=False,
)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


@current_app.task(name='tasks.scraper.check_all_product_prices', bind=True)
def check_all_product_prices(self):
    """Check prices for all active products."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(async_check_all_product_prices())


async def async_check_all_product_prices():
    """Async implementation of check_all_product_prices."""
    logger.info("Starting product price check...")

    async with async_session_maker() as session:
        try:
            product_service = ProductService(session)

            # Get products that need scraping
            products = await product_service.get_products_for_scraping(limit=50)
            logger.info(f"Found {len(products)} products to check")

            checked_count = 0
            updated_count = 0

            for product in products:
                try:
                    # Get appropriate scraper
                    scraper = get_scraper_for_url(product.url)

                    async with scraper:
                        # Scrape current product data
                        scraped_data = await scraper.scrape_product(product.url)

                        if scraped_data.price and scraped_data.price != product.current_price:
                            old_price = product.current_price

                            # Update product price
                            await product_service.update_price(
                                product.id, scraped_data.price, scraped_data.currency
                            )

                            logger.info(
                                f"Price updated for product {product.id}: "
                                f"{old_price} -> {scraped_data.price}"
                            )

                            # Check for price drop notifications TODO
                            # await check_price_drop_notifications(
                            #     session, product.id, old_price, scraped_data.price, scraped_data.currency
                            # )

                            updated_count += 1

                        # Mark as scraped
                        await product_service.mark_as_scraped(product.id)
                        checked_count += 1

                        # Add delay between scrapes to be respectful
                        await asyncio.sleep(settings.scraper_request_delay)

                except Exception as e:
                    logger.error(f"Error checking product {product.id} ({product.url}): {e}")
                    continue

            logger.info(f"Price check completed: {checked_count} checked, {updated_count} updated")
            return {"checked": checked_count, "updated": updated_count}

        except Exception as e:
            logger.error(f"Error in price check task: {e}")
            raise


async def check_price_drop_notifications(
        session, product_id: int, old_price: Optional[Decimal], new_price: Decimal, currency: str
):
    """Check if price drop triggers any notifications."""
    if not old_price or new_price >= old_price:
        return  # No price drop

    try:
        subscription_service = SubscriptionService(session)
        notification_service = NotificationService(session)

        # Get all subscriptions for this product
        subscriptions = await subscription_service.get_subscriptions_for_product(product_id)

        for subscription in subscriptions:
            should_notify = False
            notification_type = "price_drop"

            # Check price threshold
            if subscription.price_threshold and new_price <= subscription.price_threshold:
                should_notify = True
                notification_type = "price_threshold"

            # Check percentage threshold
            elif subscription.percentage_threshold:
                price_drop_percent = ((old_price - new_price) / old_price) * 100
                if price_drop_percent >= subscription.percentage_threshold:
                    should_notify = True
                    notification_type = "price_drop"

            if should_notify:
                # Create notification
                title = "Price Alert!"
                message = (
                    f"Price dropped from ${old_price} to ${new_price} {currency} "
                    f"({((old_price - new_price) / old_price) * 100:.1f}% off)"
                )

                await notification_service.create_notification(
                    user_id=subscription.user_id,
                    subscription_id=subscription.id,
                    notification_type=notification_type,
                    title=title,
                    message=message,
                    product_id=product_id,
                )

                logger.info(f"Created notification for user {subscription.user_id} on product {product_id}")

    except Exception as e:
        logger.error(f"Error checking price drop notifications: {e}")


@current_app.task(name='tasks.scraper.scrape_single_product', bind=True)
def scrape_single_product(self, product_url: str) -> dict:
    """Scrape a single product."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(async_scrape_single_product(product_url))


async def async_scrape_single_product(product_url: str) -> dict:
    """Async implementation of scrape_single_product."""
    logger.info(f"Scraping product: {product_url}")

    async with async_session_maker() as session:
        try:
            product_service = ProductService(session)

            # Check if product already exists
            existing_product = await product_service.get_by_url(product_url)

            # Get appropriate scraper
            scraper = get_scraper_for_url(product_url)

            async with scraper:
                # Scrape product data
                scraped_data = await scraper.scrape_product(product_url)

                if existing_product:
                    # Update existing product
                    if scraped_data.price and scraped_data.price != existing_product.current_price:
                        old_price = existing_product.current_price

                        await product_service.update_price(
                            existing_product.id, scraped_data.price, scraped_data.currency
                        )

                        # Check for notifications TODO
                        # await check_price_drop_notifications(
                        #     session, existing_product.id, old_price, scraped_data.price, scraped_data.currency
                        # )

                    await product_service.mark_as_scraped(existing_product.id)
                    return {"product_id": existing_product.id, "updated": True}

                else:
                    # Create new product
                    from app.schemas.product import ProductCreate

                    product_data = ProductCreate(
                        url=product_url,
                        title=scraped_data.title,
                        brand=scraped_data.brand,
                        current_price=scraped_data.price,
                        currency=scraped_data.currency,
                        store_name=scraper.name,
                        external_id=scraped_data.external_id,
                        image_url=scraped_data.image_url,
                    )

                    new_product = await product_service.create(product_data)
                    await product_service.mark_as_scraped(new_product.id)

                    return {"product_id": new_product.id, "created": True}

        except Exception as e:
            logger.error(f"Error scraping product {product_url}: {e}")
            raise

# TODO maybe remove this task
# @current_app.task(bind=True)
# def add_product_from_url(self, product_url: str, user_id: int = None):
#     """Add product from URL and optionally create subscription."""
#     try:
#         loop = asyncio.get_event_loop()
#     except RuntimeError:
#         loop = asyncio.new_event_loop()
#         asyncio.set_event_loop(loop)
#
#     return loop.run_until_complete(async_add_product_from_url(product_url, user_id))
#
#
# async def async_add_product_from_url(product_url: str, user_id: int = None):
#     """Async implementation of add_product_from_url."""
#     logger.info(f"Adding product from URL: {product_url}")
#
#     async with async_session_maker() as session:
#         try:
#             # First scrape the product
#             scrape_result = await async_scrape_single_product(product_url)
#             product_id = scrape_result["product_id"]
#
#             logger.info(f"Product added/updated with ID: {product_id}")
#             return {"product_id": product_id, "success": True}
#
#         except Exception as e:
#             logger.error(f"Error adding product from URL {product_url}: {e}")
#             raise


@current_app.task(name='tasks.scraper.check_brand_products', bind=True)
def check_brand_products(self, brand_name: str):
    """Check all products for a specific brand."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(async_check_brand_products(brand_name))


async def async_check_brand_products(brand_name: str):
    """Async implementation of check_brand_products."""
    logger.info(f"Checking products for brand: {brand_name}")

    async with async_session_maker() as session:
        try:
            product_service = ProductService(session)

            # Get all products for this brand
            products = await product_service.list_products(brand=brand_name, active_only=True)

            checked_count = 0
            updated_count = 0

            for product in products:
                try:
                    # Get appropriate scraper
                    scraper = get_scraper_for_url(product.url)

                    async with scraper:
                        # Scrape current product data
                        scraped_data = await scraper.scrape_product(product.url)

                        if scraped_data.price and scraped_data.price != product.current_price:
                            old_price = product.current_price

                            # Update product price
                            await product_service.update_price(
                                product.id, scraped_data.price, scraped_data.currency
                            )

                            # Check for brand subscription notifications TODO
                            # await check_brand_notifications(
                            #     session, brand_name, product.id, old_price, scraped_data.price, scraped_data.currency
                            # )

                            updated_count += 1

                        await product_service.mark_as_scraped(product.id)
                        checked_count += 1

                        # Add delay between scrapes
                        await asyncio.sleep(settings.scraper_request_delay)

                except Exception as e:
                    logger.error(f"Error checking brand product {product.id}: {e}")
                    continue

            logger.info(f"Brand check completed: {checked_count} checked, {updated_count} updated")
            return {"brand": brand_name, "checked": checked_count, "updated": updated_count}

        except Exception as e:
            logger.error(f"Error in brand check task: {e}")
            raise


async def check_brand_notifications(
        session, brand_name: str, product_id: int, old_price: Optional[Decimal], new_price: Decimal, currency: str
):
    """Check if price drop triggers brand subscription notifications."""
    if not old_price or new_price >= old_price:
        return

    try:
        subscription_service = SubscriptionService(session)
        notification_service = NotificationService(session)

        # Get all brand subscriptions
        subscriptions = await subscription_service.get_subscriptions_for_brand(brand_name)

        for subscription in subscriptions:
            should_notify = False
            notification_type = "price_drop"

            # Check price threshold
            if subscription.price_threshold and new_price <= subscription.price_threshold:
                should_notify = True
                notification_type = "price_threshold"

            # Check percentage threshold
            elif subscription.percentage_threshold:
                price_drop_percent = ((old_price - new_price) / old_price) * 100
                if price_drop_percent >= subscription.percentage_threshold:
                    should_notify = True
                    notification_type = "price_drop"

            if should_notify:
                # Create notification
                title = f"{brand_name} Price Alert!"
                message = (
                    f"Product price dropped from ${old_price} to ${new_price} {currency} "
                    f"({((old_price - new_price) / old_price) * 100:.1f}% off)"
                )

                await notification_service.create_notification(
                    user_id=subscription.user_id,
                    subscription_id=subscription.id,
                    notification_type=notification_type,
                    title=title,
                    message=message,
                    product_id=product_id,
                )

                logger.info(f"Created brand notification for user {subscription.user_id}")

    except Exception as e:
        logger.error(f"Error checking brand notifications: {e}")
