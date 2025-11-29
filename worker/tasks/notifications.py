# worker/tasks/notifications.py

import asyncio
import logging
import os
import random
from typing import List, Optional

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from celery import current_app
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

# Import backend components
from app.config import get_settings
from app.models.notification import Notification, NotificationStatus, NotificationType
from app.models.product import Product
from app.models.user import User
from app.services.notification import NotificationService
from app.services.product import ProductService

settings = get_settings()
logger = logging.getLogger(__name__)

# Create async engine for worker
engine = create_async_engine(
    settings.database_url.replace("postgresql://", "postgresql+asyncpg://"),
    echo=False,
)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

bot = None
# Initialize Telegram Bot #TODO
# bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
# bot = None
# if bot_token:
#     bot = Bot(
#         token=bot_token,
#         default=DefaultBotProperties(parse_mode=ParseMode.HTML)
#     )


@current_app.task(bind=True)
def process_pending_notifications(self):
    """Process all pending notifications."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(async_process_pending_notifications())


async def async_process_pending_notifications():
    """Async implementation of process_pending_notifications."""
    if not bot:
        logger.error("Telegram bot not initialized - missing TELEGRAM_BOT_TOKEN")
        # return {"error": "Bot not configured"} #TODO
    
    logger.info("Processing pending notifications...")
    
    async with async_session_maker() as session:
        try:
            notification_service = NotificationService(session)
            product_service = ProductService(session)
            
            # Get pending notifications
            notifications = await notification_service.get_pending_notifications(limit=50)
            logger.info(f"Found {len(notifications)} pending notifications")
            
            sent_count = 0
            failed_count = 0
            
            for notification in notifications:
                try:
                    # Get user data
                    user = await get_user_by_id(session, notification.user_id)
                    if not user or not user.telegram_user_id:
                        await notification_service.mark_as_failed(
                            notification.id,
                            "User not found or Telegram account not linked"
                        )
                        failed_count += 1
                        continue
                    
                    # Get product data if available
                    product = None
                    if notification.product_id:
                        product = await product_service.get_by_id(notification.product_id)
                    
                    # Send notification based on type
                    message_id = None
                    if notification.notification_type == NotificationType.PRICE_DROP:
                        message_id = await send_price_drop_notification(
                            notification, user, product
                        )
                    elif notification.notification_type == NotificationType.PRICE_THRESHOLD:
                        message_id = await send_price_threshold_notification(
                            notification, user, product
                        )
                    elif notification.notification_type == NotificationType.PRODUCT_AVAILABLE:
                        message_id = await send_product_available_notification(
                            notification, user, product
                        )
                    elif notification.notification_type == NotificationType.ERROR:
                        message_id = await send_error_notification(notification, user)
                    
                    if message_id:
                        await notification_service.mark_as_sent(notification.id, message_id)
                        sent_count += 1
                        logger.info(f"Sent notification {notification.id} to user {user.telegram_user_id}")
                    else:
                        await notification_service.mark_as_failed(
                            notification.id,
                            "Failed to send message"
                        )
                        failed_count += 1
                    
                    # Add small delay between messages
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    logger.error(f"Error processing notification {notification.id}: {e}")
                    await notification_service.mark_as_failed(
                        notification.id,
                        str(e)
                    )
                    failed_count += 1
            
            logger.info(f"Notification processing completed: {sent_count} sent, {failed_count} failed")
            return {"sent": sent_count, "failed": failed_count}
            
        except Exception as e:
            logger.error(f"Error in notification processing task: {e}")
            raise


async def get_user_by_id(session, user_id: int) -> Optional[User]:
    """Get user by ID."""
    from sqlalchemy import select
    
    stmt = select(User).where(User.id == user_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def send_price_drop_notification(
    notification: Notification, user: User, product: Optional[Product]
) -> Optional[int]:
    """Send price drop notification."""
    try:
        if not product:
            return None
        
        # Parse price information from notification message
        # This is a simplified implementation - in production you might want to store more structured data # TODO
        message_text = "🔔 <b>Price Alert!</b>\n\n"
        message_text += f"📦 <b>{product.title}</b>\n\n"
        message_text += f"{notification.message}\n\n"
        message_text += "🛒 <i>Great time to buy!</i>"
        
        # Create inline keyboard with product link
        from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
        
        keyboard_buttons = []
        if product.affiliate_link:
            keyboard_buttons.append([
                InlineKeyboardButton(text="🛒 Buy Now", url=product.affiliate_link)
            ])
        elif product.url:
            keyboard_buttons.append([
                InlineKeyboardButton(text="🔗 View Product", url=product.url)
            ])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons) if keyboard_buttons else None
        
        # Send message #TODO
        # sent_message = await bot.send_message(
        #     chat_id=user.telegram_user_id,
        #     text=message_text,
        #     reply_markup=keyboard
        # )
        # return sent_message.message_id
        mess_id = random.randint(1, 100000)
        logger.error(f"!!! Price drop notification sent to {user.telegram_user_id}. Message: {message_text}")
        return mess_id
    
    except Exception as e:
        logger.error(f"Failed to send price drop notification: {e}")
        return None


async def send_price_threshold_notification(
    notification: Notification, user: User, product: Optional[Product]
) -> Optional[int]:
    """Send price threshold notification."""
    try:
        if not product:
            return None
        
        message_text = "🎯 <b>Price Threshold Reached!</b>\n\n"
        message_text += f"📦 <b>{product.title}</b>\n\n"
        if product.current_price:
            message_text += f"💰 Current price: <b>${product.current_price}</b> {product.currency}\n"
        message_text += f"{notification.message}\n\n"
        message_text += "🛒 <i>Time to grab this deal!</i>"
        
        # Create inline keyboard
        from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
        
        keyboard_buttons = []
        if product.affiliate_link:
            keyboard_buttons.append([
                InlineKeyboardButton(text="🛒 Buy Now", url=product.affiliate_link)
            ])
        elif product.url:
            keyboard_buttons.append([
                InlineKeyboardButton(text="🔗 View Product", url=product.url)
            ])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons) if keyboard_buttons else None

        # Send message #TODO
        # sent_message = await bot.send_message(
        #     chat_id=user.telegram_user_id,
        #     text=message_text,
        #     reply_markup=keyboard
        # )
        # return sent_message.message_id
        mess_id = random.randint(1, 100000)
        logger.error(f"!!! Price drop notification sent to {user.telegram_user_id}. Message: {message_text}")
        return mess_id
    
    except Exception as e:
        logger.error(f"Failed to send threshold notification: {e}")
        return None


async def send_product_available_notification(
    notification: Notification, user: User, product: Optional[Product]
) -> Optional[int]:
    """Send product availability notification."""
    try:
        if not product:
            return None
        
        message_text = "🎉 <b>Product Available!</b>\n\n"
        message_text += f"📦 <b>{product.title}</b>\n\n"
        message_text += "✅ This product is now available for purchase!\n\n"
        message_text += "🛒 <i>Don't miss out!</i>"
        
        # Create inline keyboard
        from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
        
        keyboard_buttons = []
        if product.affiliate_link:
            keyboard_buttons.append([
                InlineKeyboardButton(text="🛒 Buy Now", url=product.affiliate_link)
            ])
        elif product.url:
            keyboard_buttons.append([
                InlineKeyboardButton(text="🔗 View Product", url=product.url)
            ])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons) if keyboard_buttons else None
        
        # Send message #TODO
        # sent_message = await bot.send_message(
        #     chat_id=user.telegram_user_id,
        #     text=message_text,
        #     reply_markup=keyboard
        # )
        # return sent_message.message_id
        mess_id = random.randint(1, 100000)
        logger.error(f"!!! Price drop notification sent to {user.telegram_user_id}. Message: {message_text}")
        return mess_id
    
    except Exception as e:
        logger.error(f"Failed to send availability notification: {e}")
        return None


async def send_error_notification(
    notification: Notification, user: User
) -> Optional[int]:
    """Send error notification."""
    try:
        message_text = "⚠️ <b>Subscription Error</b>\n\n"
        message_text += f"🆔 Subscription ID: <code>{notification.subscription_id}</code>\n\n"
        message_text += f"❌ Error: {notification.message}\n\n"
        message_text += "💡 <i>You may want to check your subscription or try again later.</i>"
        
        # Send message #TODO
        # sent_message = await bot.send_message(
        #     chat_id=user.telegram_user_id,
        #     text=message_text
        # )
        # return sent_message.message_id
        mess_id = random.randint(1, 100000)
        logger.error(f"!!! Price drop notification sent to {user.telegram_user_id}. Message: {message_text}")
        return mess_id
    
    except Exception as e:
        logger.error(f"Failed to send error notification: {e}")
        return None


@current_app.task(bind=True)
def send_notification_to_user(self, user_telegram_id: int, message: str, title: str = "Notification"):
    """Send custom notification to specific user."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(
        async_send_notification_to_user(user_telegram_id, message, title)
    )


async def async_send_notification_to_user(
    user_telegram_id: int, message: str, title: str = "Notification"
):
    """Async implementation of send_notification_to_user."""
    if not bot:
        logger.error("Telegram bot not initialized")
        # return {"error": "Bot not configured"} #TODO
    
    try:
        message_text = f"📢 <b>{title}</b>\n\n{message}"

        # TODO
        # sent_message = await bot.send_message(
        #     chat_id=user_telegram_id,
        #     text=message_text
        # )
        # return {"success": True, "message_id": sent_message.message_id}
        mess_id = random.randint(1, 100000)
        logger.error(f"!!! Price drop notification sent to {user_telegram_id}. Message: {message_text}")
        return {"success": True, "message_id": mess_id}
    
    except Exception as e:
        logger.error(f"Failed to send notification to {user_telegram_id}: {e}")
        return {"error": str(e)}


@current_app.task(bind=True)
def cleanup_old_notifications(self, days: int = 30):
    """Clean up old notifications."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(async_cleanup_old_notifications(days))


async def async_cleanup_old_notifications(days: int = 30):
    """Async implementation of cleanup_old_notifications."""
    logger.info(f"Cleaning up notifications older than {days} days...")
    
    async with async_session_maker() as session:
        try:
            notification_service = NotificationService(session)
            
            # Clean up old notifications
            deleted_count = await notification_service.cleanup_old_notifications(days)
            
            logger.info(f"Cleaned up {deleted_count} old notifications")
            return {"deleted": deleted_count}
            
        except Exception as e:
            logger.error(f"Error in cleanup task: {e}")
            raise


@current_app.task(bind=True)
def test_notification(self, user_telegram_id: int):
    """Send test notification to user."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(async_test_notification(user_telegram_id))


async def async_test_notification(user_telegram_id: int):
    """Send test notification."""
    if not bot:
        logger.error("Telegram bot not initialized")
        # return {"error": "Bot not configured"} # TODO
    
    try:
        message_text = "🧪 This is a test notification from SmartCatcher!\n\nIf you received this, notifications are working correctly."

        # TODO
        # sent_message = await bot.send_message(
        #     chat_id=user_telegram_id,
        #     text=message_text
        # )
        # return {"success": True, "message_id": sent_message.message_id}
        mess_id = random.randint(1, 100000)
        logger.error(f"!!! Price drop notification sent to {user_telegram_id}. Message: {message_text}")
        return {"success": True, "message_id": mess_id}
    
    except Exception as e:
        logger.error(f"Failed to send test notification: {e}")
        return {"error": str(e)}
