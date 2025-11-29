# bot/middlewares/auth.py

import logging
from typing import Any, Awaitable, Callable, Dict, Optional
from datetime import datetime, timedelta

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message

from utils.api_client import APIClient

logger = logging.getLogger(__name__)


class TokenStorage:
    """Simple in-memory token storage. In production, use Redis or database."""

    def __init__(self):
        self._storage: Dict[int, Dict[str, Any]] = {}

    def save_tokens(self, user_id: int, access_token: str, refresh_token: str, expires_in: int = 3600):
        """Save user tokens."""
        self._storage[user_id] = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_at": datetime.now() + timedelta(seconds=expires_in)
        }

    def get_access_token(self, user_id: int) -> Optional[str]:
        """Get user access token if not expired."""
        data = self._storage.get(user_id)
        if not data:
            return None

        if datetime.now() >= data["expires_at"]:
            return None

        return data["access_token"]

    def get_refresh_token(self, user_id: int) -> Optional[str]:
        """Get user refresh token."""
        data = self._storage.get(user_id)
        return data["refresh_token"] if data else None

    def remove_tokens(self, user_id: int):
        """Remove user tokens."""
        self._storage.pop(user_id, None)


class AuthMiddleware(BaseMiddleware):
    """Authentication middleware with token management."""

    def __init__(self, api_client: APIClient):
        self.api_client = api_client
        self.token_storage = TokenStorage()
        super().__init__()

    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message | CallbackQuery,
            data: Dict[str, Any],
    ) -> Any:
        """Process authentication middleware."""
        # Skip authentication for start/help commands
        if isinstance(event, Message):
            if event.text and event.text.startswith(("/start", "/help")):
                data["api_client"] = self.api_client
                data["token_storage"] = self.token_storage
                return await handler(event, data)

        user_id = event.from_user.id
        access_token = self.token_storage.get_access_token(user_id)

        # Try to refresh token if expired
        if not access_token:
            refresh_token = self.token_storage.get_refresh_token(user_id)
            if refresh_token:
                try:
                    token_data = await self.api_client.refresh_token(refresh_token)
                    if token_data:
                        self.token_storage.save_tokens(
                            user_id,
                            token_data["access_token"],
                            token_data.get("refresh_token", refresh_token)
                        )
                        access_token = token_data["access_token"]
                        logger.info(f"Token refreshed for user {user_id}")
                except Exception as e:
                    logger.error(f"Failed to refresh token for user {user_id}: {e}")

        # Pass data to handlers
        data["api_client"] = self.api_client
        data["token_storage"] = self.token_storage
        data["access_token"] = access_token
        data["is_authenticated"] = access_token is not None

        return await handler(event, data)