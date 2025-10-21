# backend/app/models/subscription.py

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, Relationship, SQLModel


class SubscriptionType(str, Enum):
    """Subscription type enum."""

    PRODUCT = "product"  # Subscribe to specific product
    BRAND = "brand"  # Subscribe to brand (all products from brand)


class Subscription(SQLModel, table=True):
    """Subscription model."""

    __tablename__ = "subscriptions"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True, ondelete="CASCADE")
    product_id: Optional[int] = Field(default=None, foreign_key="products.id", ondelete="CASCADE")
    subscription_type: SubscriptionType = Field(default=SubscriptionType.PRODUCT)
    brand_name: Optional[str] = Field(default=None, index=True)
    price_threshold: Optional[Decimal] = Field(default=None, decimal_places=2)
    percentage_threshold: Optional[float] = Field(default=None)  # Percentage drop
    is_active: bool = Field(default=True)
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
    user: "User" = Relationship(back_populates="subscriptions", cascade_delete=True)
    product: Optional["Product"] = Relationship(cascade_delete=True)

    def __str__(self) -> str:
        if self.subscription_type == SubscriptionType.PRODUCT:
            return f"Subscription(user_id={self.user_id}, product_id={self.product_id})"
        return f"Subscription(user_id={self.user_id}, brand={self.brand_name})"

    def __repr__(self) -> str:
        return (
            f"Subscription(id={self.id}, user_id={self.user_id}, "
            f"type={self.subscription_type}, threshold={self.price_threshold})"
        )
