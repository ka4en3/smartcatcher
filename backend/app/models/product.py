# backend/app/models/product.py

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, Relationship, SQLModel


class Product(SQLModel, table=True):
    """Product model."""

    __tablename__ = "products"

    id: Optional[int] = Field(default=None, primary_key=True)
    url: str = Field(index=True, unique=True)
    title: str = Field(index=True)
    brand: Optional[str] = Field(default=None, index=True)
    current_price: Optional[Decimal] = Field(default=None, decimal_places=2)
    currency: str = Field(default="USD", max_length=3)
    store_name: str = Field(index=True)
    external_id: Optional[str] = Field(default=None, index=True)  # Store-specific ID
    image_url: Optional[str] = Field(default=None)
    affiliate_link: Optional[str] = Field(default=None)
    is_active: bool = Field(default=True)
    last_scraped_at: Optional[datetime] = Field(default=None)
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
    price_history: list["PriceHistory"] = Relationship(back_populates="product")

    def __str__(self) -> str:
        return f"Product(id={self.id}, title={self.title}, price={self.current_price})"

    def __repr__(self) -> str:
        return (
            f"Product(id={self.id}, title={self.title}, "
            f"price={self.current_price} {self.currency})"
        )


class PriceHistory(SQLModel, table=True):
    """Price history model."""

    __tablename__ = "price_history"

    id: Optional[int] = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="products.id", index=True)
    price: Decimal = Field(decimal_places=2)
    currency: str = Field(max_length=3)
    recorded_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )

    # Relationships
    product: Product = Relationship(back_populates="price_history")

    def __str__(self) -> str:
        return f"PriceHistory(product_id={self.product_id}, price={self.price})"

    def __repr__(self) -> str:
        return (
            f"PriceHistory(id={self.id}, product_id={self.product_id}, "
            f"price={self.price} {self.currency}, recorded_at={self.recorded_at})"
        )
