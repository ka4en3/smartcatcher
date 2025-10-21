# backend/app/models/user.py

from datetime import datetime
from typing import Optional

from pydantic import EmailStr
from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, Relationship, SQLModel

from .subscription import Subscription


class User(SQLModel, table=True):
    """User model."""

    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    email: EmailStr = Field(index=True, unique=True)
    hashed_password: str
    is_active: bool = Field(default=True)
    is_admin: bool = Field(default=False)
    telegram_user_id: Optional[int] = Field(default=None, index=True)
    telegram_username: Optional[str] = Field(default=None)
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(
            DateTime(timezone=True), onupdate=func.now(), nullable=True
        ),
    )

    # Relationships
    subscriptions: list[Subscription] = Relationship(back_populates="user", cascade_delete=True)

    def __str__(self) -> str:
        return f"User(id={self.id}, email={self.email})"

    def __repr__(self) -> str:
        return f"User(id={self.id}, email={self.email}, is_active={self.is_active})"
