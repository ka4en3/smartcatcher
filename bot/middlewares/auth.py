# bot/middlewares/auth.py

import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message

from utils.api_client import APIClient

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseMiddleware):
    """Authentication middleware."""

    def __init__(self, api_client: APIClient):
        self.api_client = api_client
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any],
    ) -> Any:
        """Process authentication middleware."""
        # Skip authentication for certain commands
        if isinstance(event, Message):
            if event.text and event.text.startswith(("/start", "/help")):
                return await handler(event, data)
        
        user_id = event.from_user.id
        user_token = None
        
        try:
            # Try to get user by Telegram ID
            user_data = await self.api_client.get_user_by_telegram_id(user_id)
            
            if user_data:
                # User is linked, try to get a fresh token
                # This is a simplified approach -> might want to store tokens securely and refresh them as needed # TODO
                logger.info(f"User {user_id} is authenticated")
                # For now, we'll pass the user_data instead of token
                # The handlers will need to handle authentication differently
                data["user_data"] = user_data
                data["api_client"] = self.api_client
            else:
                logger.info(f"User {user_id} is not authenticated")
                data["user_data"] = None
                data["api_client"] = self.api_client
        
        except Exception as e:
            logger.error(f"Error in auth middleware for user {user_id}: {e}")
            data["user_data"] = None
            data["api_client"] = self.api_client
        
        return await handler(event, data)
