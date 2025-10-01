# backend/app/services/product.py

from decimal import Decimal
from typing import Optional

from sqlalchemy import desc, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.product import PriceHistory, Product
from app.schemas.product import ProductCreate, ProductUpdate


class ProductService:
    """Product service."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, product_data: ProductCreate) -> Product:
        """Create new product."""
        product = Product(**product_data.model_dump())
        self.session.add(product)
        await self.session.commit()
        await self.session.refresh(product)
        return product

    async def get_by_id(self, product_id: int) -> Optional[Product]:
        """Get product by ID."""
        stmt = select(Product).where(Product.id == product_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_url(self, url: str) -> Optional[Product]:
        """Get product by URL."""
        stmt = select(Product).where(Product.url == url)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_external_id(self, external_id: str, store_name: str) -> Optional[Product]:
        """Get product by external ID and store name."""
        stmt = select(Product).where(
            Product.external_id == external_id,
            Product.store_name == store_name
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_products(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        brand: Optional[str] = None,
        store: Optional[str] = None,
        active_only: bool = True,
    ) -> list[Product]:
        """List products with filtering."""
        stmt = select(Product)

        if active_only:
            stmt = stmt.where(Product.is_active == True)

        if search:
            stmt = stmt.where(
                or_(
                    Product.title.icontains(search),
                    Product.brand.icontains(search) if Product.brand else False,
                )
            )

        if brand:
            stmt = stmt.where(Product.brand == brand)

        if store:
            stmt = stmt.where(Product.store_name == store)

        stmt = stmt.offset(skip).limit(limit).order_by(desc(Product.created_at))

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update(self, product_id: int, product_update: ProductUpdate) -> Product:
        """Update product."""
        product = await self.get_by_id(product_id)
        if not product:
            raise ValueError("Product not found")

        update_data = product_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(product, field, value)

        await self.session.commit()
        await self.session.refresh(product)
        return product

    async def update_price(
        self, product_id: int, new_price: Decimal, currency: str = "USD"
    ) -> tuple[Product, PriceHistory]:
        """Update product price and create price history entry."""
        product = await self.get_by_id(product_id)
        if not product:
            raise ValueError("Product not found")

        # Update product current price
        old_price = product.current_price
        product.current_price = new_price
        product.currency = currency

        # Create price history entry
        price_history = PriceHistory(
            product_id=product_id,
            price=new_price,
            currency=currency,
        )
        self.session.add(price_history)

        await self.session.commit()
        await self.session.refresh(product)
        await self.session.refresh(price_history)

        return product, price_history

    async def get_price_history(
        self, product_id: int, skip: int = 0, limit: int = 100
    ) -> list[PriceHistory]:
        """Get product price history."""
        stmt = (
            select(PriceHistory)
            .where(PriceHistory.product_id == product_id)
            .order_by(desc(PriceHistory.recorded_at))
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_products_for_scraping(self, limit: int = 100) -> list[Product]:
        """Get products that need price updates."""
        stmt = (
            select(Product)
            .where(Product.is_active == True)
            .order_by(Product.last_scraped_at.asc().nullsfirst())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def mark_as_scraped(self, product_id: int) -> None:
        """Mark product as recently scraped."""
        from datetime import datetime
        
        product = await self.get_by_id(product_id)
        if product:
            product.last_scraped_at = datetime.utcnow()
            await self.session.commit()
