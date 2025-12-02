# bot/main.py

import asyncio
import logging
import sys
import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from handlers import start, subscription
from middlewares.auth import AuthMiddleware
from utils.api_client import APIClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)

logger = logging.getLogger(__name__)


async def main() -> None:
    """Main bot function."""
    # Get bot token from environment
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        logger.error("TELEGRAM_BOT_TOKEN environment variable not set")
        return

    backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")

    # Initialize bot and dispatcher
    bot = Bot(
        token=bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Initialize API client
    api_client = APIClient(backend_url)

    # Setup middleware
    auth_middleware = AuthMiddleware(api_client)
    dp.message.middleware(auth_middleware)
    dp.callback_query.middleware(auth_middleware)

    # Include routers
    dp.include_router(start.router)
    dp.include_router(subscription.router)

    # Store API client in dispatcher data
    dp["api_client"] = api_client

    try:
        logger.info("Starting bot...")
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        await api_client.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")