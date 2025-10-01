# backend/app/services/subscription.py

from typing import Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.subscription import Subscription, SubscriptionType
from app.schemas.subscription import SubscriptionCreate, SubscriptionUpdate
from app.services.product import ProductService


class SubscriptionService:
    """Subscription service."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.product_service = ProductService(session)

    async def create_subscription(
        self, user_id: int, subscription_data: SubscriptionCreate
    ) -> Subscription:
        """Create new subscription."""
        # Handle product subscription
        if subscription_data.subscription_type == SubscriptionType.PRODUCT:
            product_id = subscription_data.product_id
            
            # If product_url is provided, find or create product
            if subscription_data.product_url and not product_id:
                product = await self.product_service.get_by_url(subscription_data.product_url)
                if not product:
                    # For now, raise an error. In production, you might want to
                    # automatically scrape and create the product
                    raise ValueError(
                        "Product not found. Please add the product first or provide product_id."
                    )
                product_id = product.id

            subscription = Subscription(
                user_id=user_id,
                product_id=product_id,
                subscription_type=subscription_data.subscription_type,
                price_threshold=subscription_data.price_threshold,
                percentage_threshold=subscription_data.percentage_threshold,
                is_active=True,
            )
        
        # Handle brand subscription
        elif subscription_data.subscription_type == SubscriptionType.BRAND:
            subscription = Subscription(
                user_id=user_id,
                subscription_type=subscription_data.subscription_type,
                brand_name=subscription_data.brand_name,
                price_threshold=subscription_data.price_threshold,
                percentage_threshold=subscription_data.percentage_threshold,
                is_active=True,
            )
        
        else:
            raise ValueError("Invalid subscription type")

        self.session.add(subscription)
        await self.session.commit()
        await self.session.refresh(subscription)
        return subscription

    async def get_by_id(self, subscription_id: int) -> Optional[Subscription]:
        """Get subscription by ID."""
        stmt = (
            select(Subscription)
            .where(Subscription.id == subscription_id)
            .options(selectinload(Subscription.product))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_user_subscriptions(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True,
    ) -> list[Subscription]:
        """List user subscriptions."""
        stmt = select(Subscription).where(Subscription.user_id == user_id)
        
        if active_only:
            stmt = stmt.where(Subscription.is_active == True)

        stmt = (
            stmt.options(selectinload(Subscription.product))
            .offset(skip)
            .limit(limit)
            .order_by(Subscription.created_at.desc())
        )

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update(
        self, subscription_id: int, subscription_update: SubscriptionUpdate
    ) -> Subscription:
        """Update subscription."""
        subscription = await self.get_by_id(subscription_id)
        if not subscription:
            raise ValueError("Subscription not found")

        update_data = subscription_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(subscription, field, value)

        await self.session.commit()
        await self.session.refresh(subscription)
        return subscription

    async def delete(self, subscription_id: int) -> bool:
        """Delete subscription (soft delete by setting is_active to False)."""
        subscription = await self.get_by_id(subscription_id)
        if not subscription:
            return False

        subscription.is_active = False
        await self.session.commit()
        return True

    async def get_subscriptions_for_product(self, product_id: int) -> list[Subscription]:
        """Get all active subscriptions for a product."""
        stmt = (
            select(Subscription)
            .where(
                and_(
                    Subscription.product_id == product_id,
                    Subscription.is_active == True,
                )
            )
            .options(selectinload(Subscription.user))
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_subscriptions_for_brand(self, brand_name: str) -> list[Subscription]:
        """Get all active subscriptions for a brand."""
        stmt = (
            select(Subscription)
            .where(
                and_(
                    Subscription.brand_name == brand_name,
                    Subscription.subscription_type == SubscriptionType.BRAND,
                    Subscription.is_active == True,
                )
            )
            .options(selectinload(Subscription.user))
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
