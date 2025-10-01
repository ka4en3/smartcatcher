# backend/app/schemas/product.py

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, HttpUrl, ConfigDict


class ProductBase(BaseModel):
    """Base product schema."""

    url: str
    title: str
    brand: Optional[str] = None
    currency: str = "USD"
    store_name: str


class ProductCreate(ProductBase):
    """Product creation schema."""

    current_price: Optional[Decimal] = None
    external_id: Optional[str] = None
    image_url: Optional[str] = None
    affiliate_link: Optional[str] = None


class ProductUpdate(BaseModel):
    """Product update schema."""

    title: Optional[str] = None
    brand: Optional[str] = None
    current_price: Optional[Decimal] = None
    currency: Optional[str] = None
    image_url: Optional[str] = None
    affiliate_link: Optional[str] = None
    is_active: Optional[bool] = None


class ProductRead(ProductBase):
    """Product read schema."""

    id: int
    current_price: Optional[Decimal] = None
    external_id: Optional[str] = None
    image_url: Optional[str] = None
    affiliate_link: Optional[str] = None
    is_active: bool
    last_scraped_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class PriceHistoryRead(BaseModel):
    """Price history read schema."""

    id: int
    product_id: int
    price: Decimal
    currency: str
    recorded_at: datetime

    model_config = ConfigDict(from_attributes=True)
