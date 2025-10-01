# backend/app/services/notification.py

from datetime import datetime
from typing import Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification, NotificationStatus, NotificationType


class NotificationService:
    """Notification service."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_notification(
        self,
        user_id: int,
        subscription_id: int,
        notification_type: NotificationType,
        title: str,
        message: str,
        product_id: Optional[int] = None,
    ) -> Notification:
        """Create new notification."""
        notification = Notification(
            user_id=user_id,
            subscription_id=subscription_id,
            product_id=product_id,
            notification_type=notification_type,
            title=title,
            message=message,
            status=NotificationStatus.PENDING,
        )

        self.session.add(notification)
        await self.session.commit()
        await self.session.refresh(notification)
        return notification

    async def get_by_id(self, notification_id: int) -> Optional[Notification]:
        """Get notification by ID."""
        stmt = select(Notification).where(Notification.id == notification_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_pending_notifications(self, limit: int = 100) -> list[Notification]:
        """Get pending notifications for processing."""
        stmt = (
            select(Notification)
            .where(Notification.status == NotificationStatus.PENDING)
            .order_by(Notification.created_at)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def mark_as_sent(
        self, notification_id: int, telegram_message_id: Optional[int] = None
    ) -> Notification:
        """Mark notification as sent."""
        notification = await self.get_by_id(notification_id)
        if not notification:
            raise ValueError("Notification not found")

        notification.status = NotificationStatus.SENT
        notification.sent_at = datetime.utcnow()
        if telegram_message_id:
            notification.telegram_message_id = telegram_message_id

        await self.session.commit()
        await self.session.refresh(notification)
        return notification

    async def mark_as_failed(
        self, notification_id: int, error_message: str
    ) -> Notification:
        """Mark notification as failed."""
        notification = await self.get_by_id(notification_id)
        if not notification:
            raise ValueError("Notification not found")

        notification.status = NotificationStatus.FAILED
        notification.error_message = error_message

        await self.session.commit()
        await self.session.refresh(notification)
        return notification

    async def get_user_notifications(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        notification_type: Optional[NotificationType] = None,
    ) -> list[Notification]:
        """Get user notifications."""
        stmt = select(Notification).where(Notification.user_id == user_id)

        if notification_type:
            stmt = stmt.where(Notification.notification_type == notification_type)

        stmt = (
            stmt.order_by(Notification.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def cleanup_old_notifications(self, days: int = 30) -> int:
        """Clean up old notifications."""
        from datetime import timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        stmt = select(Notification).where(
            and_(
                Notification.created_at < cutoff_date,
                Notification.status == NotificationStatus.SENT,
            )
        )
        
        result = await self.session.execute(stmt)
        notifications_to_delete = result.scalars().all()
        
        for notification in notifications_to_delete:
            await self.session.delete(notification)
        
        await self.session.commit()
        return len(notifications_to_delete)
