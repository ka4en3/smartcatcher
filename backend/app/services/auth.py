# backend/app/services/auth.py

from datetime import timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationException
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.models.user import User
from app.services.user import UserService


class AuthService:
    """Authentication service."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_service = UserService(session)

    async def create_user(self, email: str, password: str) -> User:
        """Create new user with hashed password."""
        hashed_password = get_password_hash(password)
        user_data = {
            "email": email,
            "hashed_password": hashed_password,
            "is_active": True,
            "is_admin": False,
        }
        return await self.user_service.create(user_data)

    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user by email and password."""
        user = await self.user_service.get_by_email(email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        return await self.user_service.get_by_email(email)

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create access token."""
        subject = data.get("sub")
        return create_access_token(subject, expires_delta)

    def create_refresh_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create refresh token."""
        subject = data.get("sub")
        return create_refresh_token(subject, expires_delta)

    async def refresh_tokens(self, refresh_token: str) -> tuple[str, str]:
        """Refresh access and refresh tokens."""
        try:
            payload = decode_token(refresh_token)
            token_type = payload.get("type")
            
            if token_type != "refresh":
                raise AuthenticationException("Invalid token type")
            
            user_id = payload.get("sub")
            if not user_id:
                raise AuthenticationException("Invalid token payload")
            
            # Verify user still exists and is active
            user = await self.user_service.get_by_id(int(user_id))
            if not user or not user.is_active:
                raise AuthenticationException("User not found or inactive")
            
            # Create new tokens
            new_access_token = create_access_token(user_id)
            new_refresh_token = create_refresh_token(user_id)
            
            return new_access_token, new_refresh_token
            
        except Exception as e:
            raise AuthenticationException("Invalid refresh token") from e
