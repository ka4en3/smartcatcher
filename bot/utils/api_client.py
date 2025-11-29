# bot/utils/api_client.py

import logging
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


class APIClient:
    """API client for backend communication."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self) -> None:
        """Close HTTP client."""
        await self.client.aclose()

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        token: Optional[str] = None,
    ) -> Optional[Dict]:
        """Make HTTP request to backend."""
        url = f"{self.base_url}{endpoint}"
        
        request_headers = {"Content-Type": "application/json"}
        if headers:
            request_headers.update(headers)
        
        if token:
            request_headers["Authorization"] = f"Bearer {token}"

        try:
            response = await self.client.request(
                method=method,
                url=url,
                json=data,
                headers=request_headers,
            )
            
            if response.status_code in [200, 201]:
                return response.json()
            elif response.status_code == 204:
                return {"success": True}
            else:
                logger.error(f"API request failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"API request error: {e}")
            return None

    async def register(self, email: str, password: str) -> Optional[Dict]:
        """Register new user."""
        data = {"email": email, "password": password}
        return await self._make_request("POST", "/auth/register", data)

    async def login(self, email: str, password: str) -> Optional[Dict]:
        """Login user."""
        data = {"username": email, "password": password}
        return await self._make_request("POST", "/auth/login", data)

    async def refresh_token(self, refresh_token: str) -> Optional[Dict]:
        """Refresh access token."""
        data = {"refresh_token": refresh_token}
        return await self._make_request("POST", "/auth/refresh", data)

    async def get_user_by_telegram_id(self, telegram_user_id: int) -> Optional[Dict]:
        """Get user by Telegram ID."""
        # This endpoint doesn't exist in API yet, need to implement it # TODO
        # For now, return None
        logger.warning("get_user_by_telegram_id not implemented in backend")
        return None

    async def link_telegram_account(
        self, access_token: str, telegram_user_id: int, telegram_username: Optional[str] = None
    ) -> bool:
        """Link Telegram account to user."""
        data = {
            "telegram_user_id": telegram_user_id,
            "telegram_username": telegram_username,
        }
        
        result = await self._make_request(
            "PATCH", "/users/me", data, token=access_token
        )
        return result is not None

    async def get_user_profile(self, access_token: str) -> Optional[Dict]:
        """Get user profile."""
        return await self._make_request("GET", "/users/me", token=access_token)

    async def create_subscription(
        self, access_token: str, subscription_data: Dict
    ) -> Optional[Dict]:
        """Create subscription."""
        return await self._make_request(
            "POST", "/subscriptions", subscription_data, token=access_token
        )

    async def get_user_subscriptions(self, access_token: str) -> Optional[List[Dict]]:
        """Get user subscriptions."""
        return await self._make_request("GET", "/subscriptions", token=access_token)

    async def delete_subscription(self, access_token: str, subscription_id: int) -> bool:
        """Delete subscription."""
        result = await self._make_request(
            "DELETE", f"/subscriptions/{subscription_id}", token=access_token
        )
        return result is not None

    async def get_product(self, access_token: str, product_id: int) -> Optional[Dict]:
        """Get product details."""
        return await self._make_request(
            "GET", f"/products/{product_id}", token=access_token
        )

    async def get_products(
        self,
        access_token: str,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
    ) -> Optional[List[Dict]]:
        """Get products list."""
        params = {"skip": skip, "limit": limit}
        if search:
            params["search"] = search
        
        # Convert params to query string
        query_params = "&".join([f"{k}={v}" for k, v in params.items()])
        endpoint = f"/products?{query_params}"
        
        return await self._make_request("GET", endpoint, token=access_token)
