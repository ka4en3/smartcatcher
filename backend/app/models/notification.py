# backend/app/models/notification.py

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Column, DateTime, func, Text
from sqlmodel import Field, SQLModel


class NotificationType(str, Enum):
    """Notification type enum."""

    PRICE_DROP = "price_drop"
    PRICE_THRESHOLD = "price_threshold"
    PRODUCT_AVAILABLE = "product_available"
    ERROR = "error"


class NotificationStatus(str, Enum):
    """Notification status enum."""

    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class Notification(SQLModel, table=True):
    """Notification model."""

    __tablename__ = "notifications"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True, ondelete="CASCADE")
    subscription_id: int = Field(foreign_key="subscriptions.id", index=True)
    product_id: Optional[int] = Field(default=None, foreign_key="products.id", ondelete="CASCADE")
    notification_type: NotificationType = Field(index=True)
    status: NotificationStatus = Field(default=NotificationStatus.PENDING, index=True)
    title: str
    message: str = Field(sa_column=Column(Text))
    telegram_message_id: Optional[int] = Field(default=None)
    error_message: Optional[str] = Field(default=None)
    sent_at: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )

    def __str__(self) -> str:
        return f"Notification(id={self.id}, type={self.notification_type}, status={self.status})"

    def __repr__(self) -> str:
        return (
            f"Notification(id={self.id}, user_id={self.user_id}, "
            f"type={self.notification_type}, status={self.status})"
        )
