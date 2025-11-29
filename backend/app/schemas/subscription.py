# backend/app/schemas/subscription.py

from decimal import Decimal
from typing import Optional, Self

from pydantic import BaseModel, ConfigDict, model_validator

from app.models.subscription import SubscriptionType


class SubscriptionBase(BaseModel):
    """Base subscription schema."""

    subscription_type: SubscriptionType = SubscriptionType.PRODUCT
    price_threshold: Optional[Decimal] = None
    percentage_threshold: Optional[float] = None

    # Use ConfigDict for Pydantic V2
    model_config = ConfigDict(use_enum_values=True)


class SubscriptionCreate(SubscriptionBase):
    """Subscription creation schema."""

    product_url: Optional[str] = None
    product_id: Optional[int] = None
    brand_name: Optional[str] = None

    @model_validator(mode="after")
    def validate_subscription_target(self) -> "Self":
        """Cross-field validation: ensure correct fields are set based on subscription type."""
        subscription_type = self.subscription_type

        if subscription_type == SubscriptionType.PRODUCT:
            if not self.product_id and not self.product_url:
                raise ValueError("For product subscriptions, either 'product_id' or 'product_url' must be provided.")
            if self.brand_name:
                raise ValueError("brand_name should not be set for product-type subscriptions")

        elif subscription_type == SubscriptionType.BRAND:
            if not self.brand_name:
                raise ValueError("For brand subscriptions, 'brand_name' is required.")
            if self.product_id or self.product_url:
                raise ValueError("product_id and product_url should not be set for brand-type subscriptions")

        return self

    @model_validator(mode="after")
    def at_least_one_threshold(self) -> "Self":
        """Ensure at least one threshold is provided."""
        if not self.price_threshold and not self.percentage_threshold:
            raise ValueError("Either 'price_threshold' or 'percentage_threshold' must be provided.")
        return self


class SubscriptionUpdate(BaseModel):
    """Subscription update schema."""

    price_threshold: Optional[Decimal] = None
    percentage_threshold: Optional[float] = None
    is_active: Optional[bool] = None


class SubscriptionRead(SubscriptionBase):
    """Subscription read schema."""

    id: int
    user_id: int
    product_id: Optional[int] = None
    brand_name: Optional[str] = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
