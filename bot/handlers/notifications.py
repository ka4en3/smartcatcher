# bot/handlers/notifications.py

import logging
from typing import Any

from aiogram import Router, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from utils.api_client import APIClient

logger = logging.getLogger(__name__)
router = Router()


async def send_price_drop_notification(
    bot: types.Bot,
    user_telegram_id: int,
    product_title: str,
    old_price: float,
    new_price: float,
    currency: str,
    product_url: str,
    affiliate_link: str = None
) -> int:
    """Send price drop notification to user."""
    try:
        # Calculate discount
        discount_amount = old_price - new_price
        discount_percent = (discount_amount / old_price) * 100 if old_price > 0 else 0
        
        # Format notification message
        message_text = "🔔 <b>Price Alert!</b>\n\n"
        message_text += f"📦 <b>{product_title}</b>\n\n"
        message_text += f"💰 Price dropped by <b>${discount_amount:.2f} ({discount_percent:.1f}%)</b>\n"
        message_text += f"❌ Was: <s>${old_price:.2f}</s> {currency}\n"
        message_text += f"✅ Now: <b>${new_price:.2f}</b> {currency}\n\n"
        message_text += "🛒 <i>Great time to buy!</i>"
        
        # Create keyboard with buy link
        keyboard_buttons = []
        
        if affiliate_link:
            keyboard_buttons.append([
                InlineKeyboardButton(text="🛒 Buy Now", url=affiliate_link)
            ])
        elif product_url:
            keyboard_buttons.append([
                InlineKeyboardButton(text="🔗 View Product", url=product_url)
            ])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons) if keyboard_buttons else None
        
        # Send message
        sent_message = await bot.send_message(
            chat_id=user_telegram_id,
            text=message_text,
            reply_markup=keyboard
        )
        
        return sent_message.message_id
    
    except Exception as e:
        logger.error(f"Failed to send price drop notification to {user_telegram_id}: {e}")
        return None


async def send_threshold_notification(
    bot: types.Bot,
    user_telegram_id: int,
    product_title: str,
    current_price: float,
    threshold: float,
    currency: str,
    product_url: str,
    affiliate_link: str = None
) -> int:
    """Send threshold reached notification to user."""
    try:
        # Format notification message
        message_text = "🎯 <b>Price Threshold Reached!</b>\n\n"
        message_text += f"📦 <b>{product_title}</b>\n\n"
        message_text += f"💰 Current price: <b>${current_price:.2f}</b> {currency}\n"
        message_text += f"🎯 Your threshold: <b>${threshold:.2f}</b> {currency}\n\n"
        message_text += "🛒 <i>Time to grab this deal!</i>"
        
        # Create keyboard with buy link
        keyboard_buttons = []
        
        if affiliate_link:
            keyboard_buttons.append([
                InlineKeyboardButton(text="🛒 Buy Now", url=affiliate_link)
            ])
        elif product_url:
            keyboard_buttons.append([
                InlineKeyboardButton(text="🔗 View Product", url=product_url)
            ])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons) if keyboard_buttons else None
        
        # Send message
        sent_message = await bot.send_message(
            chat_id=user_telegram_id,
            text=message_text,
            reply_markup=keyboard
        )
        
        return sent_message.message_id
    
    except Exception as e:
        logger.error(f"Failed to send threshold notification to {user_telegram_id}: {e}")
        return None


async def send_error_notification(
    bot: types.Bot,
    user_telegram_id: int,
    error_message: str,
    subscription_id: int = None
) -> int:
    """Send error notification to user."""
    try:
        # Format notification message
        message_text = "⚠️ <b>Subscription Error</b>\n\n"
        if subscription_id:
            message_text += f"🆔 Subscription ID: <code>{subscription_id}</code>\n\n"
        message_text += f"❌ Error: {error_message}\n\n"
        message_text += "💡 <i>You may want to check your subscription or try again later.</i>"
        
        # Send message
        sent_message = await bot.send_message(
            chat_id=user_telegram_id,
            text=message_text
        )
        
        return sent_message.message_id
    
    except Exception as e:
        logger.error(f"Failed to send error notification to {user_telegram_id}: {e}")
        return None


async def send_product_available_notification(
    bot: types.Bot,
    user_telegram_id: int,
    product_title: str,
    product_url: str,
    affiliate_link: str = None
) -> int:
    """Send product availability notification to user."""
    try:
        # Format notification message
        message_text = "🎉 <b>Product Available!</b>\n\n"
        message_text += f"📦 <b>{product_title}</b>\n\n"
        message_text += "✅ This product is now available for purchase!\n\n"
        message_text += "🛒 <i>Don't miss out!</i>"
        
        # Create keyboard with buy link
        keyboard_buttons = []
        
        if affiliate_link:
            keyboard_buttons.append([
                InlineKeyboardButton(text="🛒 Buy Now", url=affiliate_link)
            ])
        elif product_url:
            keyboard_buttons.append([
                InlineKeyboardButton(text="🔗 View Product", url=product_url)
            ])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons) if keyboard_buttons else None
        
        # Send message
        sent_message = await bot.send_message(
            chat_id=user_telegram_id,
            text=message_text,
            reply_markup=keyboard
        )
        
        return sent_message.message_id
    
    except Exception as e:
        logger.error(f"Failed to send availability notification to {user_telegram_id}: {e}")
        return None


# Export notification functions for use by worker tasks
__all__ = [
    "send_price_drop_notification",
    "send_threshold_notification", 
    "send_error_notification",
    "send_product_available_notification",
]
