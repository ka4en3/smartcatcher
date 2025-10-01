# backend/app/schemas/user.py

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, ConfigDict


class UserBase(BaseModel):
    """Base user schema."""

    email: EmailStr


class UserCreate(UserBase):
    """User creation schema."""

    password: str


class UserUpdate(BaseModel):
    """User update schema."""

    email: Optional[EmailStr] = None
    password: Optional[str] = None
    telegram_user_id: Optional[int] = None
    telegram_username: Optional[str] = None


class UserRead(UserBase):
    """User read schema."""

    id: int
    is_active: bool
    is_admin: bool
    telegram_user_id: Optional[int] = None
    telegram_username: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
