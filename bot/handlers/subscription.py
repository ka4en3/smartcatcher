# bot/handlers/subscription.py

import logging
import re
from typing import Any

from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from utils.api_client import APIClient

logger = logging.getLogger(__name__)
router = Router()


class SubscriptionStates(StatesGroup):
    """Subscription states."""
    waiting_for_threshold = State()


@router.message(Command("subscribe"))
async def subscribe_command(message: types.Message, state: FSMContext, api_client: APIClient, user_token: str = None) -> None:
    """Handle /subscribe command."""
    if not user_token:
        await message.answer("❌ Please link your account first using /start")
        return
    
    # Extract URL from command
    command_parts = message.text.split(" ", 1)
    if len(command_parts) < 2:
        help_text = "🔗 <b>Subscribe to Product</b>\n\n"
        help_text += "Please provide a product URL:\n"
        help_text += "<code>/subscribe https://www.ebay.com/itm/123456789</code>\n\n"
        help_text += "<b>Supported sites:</b>\n"
        help_text += "• eBay (ebay.com)\n"
        help_text += "• Etsy (etsy.com)\n"
        help_text += "• WebScraper.io test sites\n"
        help_text += "• Demo URLs (demo://)"
        
        await message.answer(help_text)
        return
    
    product_url = command_parts[1].strip()
    
    # Validate URL format
    url_pattern = r'https?://[^\s]+'
    if not re.match(url_pattern, product_url) and not product_url.startswith("demo://"):
        await message.answer("❌ Invalid URL format. Please provide a valid HTTP/HTTPS URL.")
        return
    
    # Store URL in state
    await state.update_data(product_url=product_url)
    
    # Ask for price threshold
    threshold_text = "💰 <b>Set Price Threshold</b>\n\n"
    threshold_text += f"Product URL: <code>{product_url}</code>\n\n"
    threshold_text += "Please set a price threshold. You'll be notified when the price drops below this amount.\n\n"
    threshold_text += "Enter threshold amount (e.g., <code>100</code> or <code>99.99</code>):"
    
    await message.answer(threshold_text)
    await state.set_state(SubscriptionStates.waiting_for_threshold)


@router.message(SubscriptionStates.waiting_for_threshold)
async def process_threshold(message: types.Message, state: FSMContext, api_client: APIClient, user_token: str = None) -> None:
    """Process price threshold."""
    if not user_token:
        await message.answer("❌ Authentication lost. Please start over with /start")
        await state.clear()
        return
    
    try:
        # Parse threshold
        threshold_text = message.text.strip()
        
        # Remove currency symbols
        threshold_text = re.sub(r'[^\d.,]', '', threshold_text)
        threshold_text = threshold_text.replace(',', '')
        
        threshold = float(threshold_text)
        if threshold <= 0:
            await message.answer("❌ Threshold must be greater than 0. Please try again.")
            return
        
        # Get stored URL
        data = await state.get_data()
        product_url = data.get("product_url")
        
        if not product_url:
            await message.answer("❌ Session expired. Please start over with /subscribe")
            await state.clear()
            return


        # TODO: create new product by url if not exists in db

        #             ALLOWED_STORE_DOMAINS = {
        #                 "amazon.com", "amazon.de", "ebay.com", "ebay.de",
        #                 "example.com",
        #             }
        #
        #             def is_allowed_store(url: str) -> bool:
        #                 try:
        #                     host = (urlparse(url).hostname or "").lower()
        #                     if host.startswith("www."):
        #                         host = host[4:]
        #                     return host in ALLOWED_STORE_DOMAINS
        #                 except Exception:
        #                     return False
        #
        #             @router.message(F.text)
        #             async def handle_product_url(message: types.Message):
        #                 url = message.text.strip()
        #
        #                 # easy check if it is a URL
        #                 if not (url.startswith("http://") or url.startswith("https://")):
        #                     return  # ignore; send a hint
        #
        #                 if not is_allowed_store(url):
        #                     await message.answer("This store is not supported yet.")
        #                     return
        #
        #                 # need user token
        #                 access_token = await get_user_access_token_by_telegram_id(message.from_user.id)  # to implement
        #
        #                 async with httpx.AsyncClient(timeout=15.0) as client:
        #                     resp = await client.post(
        #                         f"{BOT_API_BASE}/products/by-url",
        #                         json={"url": url},
        #                         headers={"Authorization": f"Bearer {access_token}"}
        #                     )
        #
        #                 if resp.status_code in (200, 201):
        #                     data = resp.json()
        #                     price = data.get("current_price")
        #                     title = data.get("title") or "Product"
        #                     await message.answer(f"Added: {title}\nPrice: {price}")
        #                 else:
        #                     err = resp.text
        #                     await message.answer(f"Failed to add product. Reason: {err[:300]}")


        # Create subscription
        subscription_data = {
            "product_url": product_url,
            "subscription_type": "product",
            "price_threshold": threshold
        }
        
        loading_msg = await message.answer("⏳ Creating subscription...")
        
        try:
            subscription = await api_client.create_subscription(user_token, subscription_data)
            
            if subscription:
                success_text = "✅ <b>Subscription Created!</b>\n\n"
                success_text += f"🔗 URL: <code>{product_url[:50]}...</code>\n"
                success_text += f"💰 Threshold: <code>${threshold:.2f}</code>\n"
                success_text += f"🆔 Subscription ID: <code>{subscription['id']}</code>\n\n"
                success_text += "🔔 You'll receive notifications when the price drops below your threshold!"
                
                await loading_msg.edit_text(success_text)
                await state.clear()
            else:
                await loading_msg.edit_text("❌ Failed to create subscription. The product might not be found or already tracked.")
        
        except Exception as e:
            logger.error(f"Error creating subscription: {e}")
            error_text = "❌ Failed to create subscription.\n\n"
            if "not found" in str(e).lower():
                error_text += "The product URL might be invalid or the product is not available."
            else:
                error_text += "Please try again later or contact support."
            
            await loading_msg.edit_text(error_text)
    
    except ValueError:
        await message.answer("❌ Invalid threshold format. Please enter a valid number (e.g., 100 or 99.99).")
    except Exception as e:
        logger.error(f"Error processing threshold: {e}")
        await message.answer("❌ An error occurred. Please try again.")


@router.message(Command("list"))
async def list_subscriptions(message: types.Message, api_client: APIClient, user_token: str = None) -> None:
    """Handle /list command."""
    if not user_token:
        await message.answer("❌ Please link your account first using /start")
        return
    
    try:
        subscriptions = await api_client.get_user_subscriptions(user_token)
        
        if not subscriptions:
            empty_text = "📭 <b>No Subscriptions</b>\n\n"
            empty_text += "You don't have any active subscriptions yet.\n"
            empty_text += "Use /subscribe to start tracking product prices!"
            
            await message.answer(empty_text)
            return
        
        # Format subscriptions list
        list_text = f"📋 <b>Your Subscriptions ({len(subscriptions)})</b>\n\n"
        
        for i, sub in enumerate(subscriptions, 1):
            product_id = sub.get("product_id")
            threshold = sub.get("price_threshold")
            subscription_id = sub.get("id")
            
            list_text += f"<b>{i}.</b> "
            
            if product_id:
                # Try to get product details
                try:
                    product = await api_client.get_product(user_token, product_id)
                    if product:
                        title = product.get("title", "Unknown Product")[:40]
                        current_price = product.get("current_price")
                        currency = product.get("currency", "USD")
                        
                        list_text += f"<code>{title}</code>\n"
                        if current_price:
                            list_text += f"   💰 Current: ${current_price} {currency}\n"
                        if threshold:
                            list_text += f"   🎯 Threshold: ${threshold}\n"
                        list_text += f"   🆔 ID: <code>{subscription_id}</code>\n\n"
                    else:
                        list_text += f"Product ID: {product_id}\n"
                        list_text += f"   🎯 Threshold: ${threshold}\n"
                        list_text += f"   🆔 ID: <code>{subscription_id}</code>\n\n"
                except Exception:
                    list_text += f"Product ID: {product_id}\n"
                    list_text += f"   🎯 Threshold: ${threshold}\n"
                    list_text += f"   🆔 ID: <code>{subscription_id}</code>\n\n"
            else:
                list_text += f"Subscription ID: {subscription_id}\n"
                if threshold:
                    list_text += f"   🎯 Threshold: ${threshold}\n\n"
        
        list_text += "💡 Use <code>/unsubscribe &lt;ID&gt;</code> to remove a subscription."
        
        # Split message if too long
        if len(list_text) > 4000:
            parts = [list_text[i:i+4000] for i in range(0, len(list_text), 4000)]
            for part in parts:
                await message.answer(part)
        else:
            await message.answer(list_text)
    
    except Exception as e:
        logger.error(f"Error listing subscriptions: {e}")
        await message.answer("❌ Failed to get subscriptions. Please try again later.")


@router.message(Command("unsubscribe"))
async def unsubscribe_command(message: types.Message, api_client: APIClient, user_token: str = None) -> None:
    """Handle /unsubscribe command."""
    if not user_token:
        await message.answer("❌ Please link your account first using /start")
        return
    
    # Extract subscription ID from command
    command_parts = message.text.split(" ", 1)
    if len(command_parts) < 2:
        help_text = "🗑️ <b>Unsubscribe</b>\n\n"
        help_text += "Please provide a subscription ID:\n"
        help_text += "<code>/unsubscribe 123</code>\n\n"
        help_text += "💡 Use /list to see your subscriptions with their IDs."
        
        await message.answer(help_text)
        return
    
    try:
        subscription_id = int(command_parts[1].strip())
        
        # Confirm unsubscribe
        confirm_text = f"❓ <b>Confirm Unsubscribe</b>\n\n"
        confirm_text += f"Are you sure you want to unsubscribe from subscription <code>{subscription_id}</code>?"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Yes, Unsubscribe", 
                    callback_data=f"unsubscribe_{subscription_id}"
                ),
                InlineKeyboardButton(
                    text="❌ Cancel", 
                    callback_data="cancel_unsubscribe"
                )
            ]
        ])
        
        await message.answer(confirm_text, reply_markup=keyboard)
    
    except ValueError:
        await message.answer("❌ Invalid subscription ID. Please provide a valid number.")
    except Exception as e:
        logger.error(f"Error processing unsubscribe command: {e}")
        await message.answer("❌ An error occurred. Please try again.")


@router.callback_query(lambda c: c.data.startswith("unsubscribe_"))
async def confirm_unsubscribe(callback: types.CallbackQuery, api_client: APIClient, user_token: str = None) -> None:
    """Handle unsubscribe confirmation."""
    if not user_token:
        await callback.message.edit_text("❌ Authentication lost. Please start over with /start")
        await callback.answer()
        return
    
    try:
        subscription_id = int(callback.data.split("_")[1])
        
        # Delete subscription
        success = await api_client.delete_subscription(user_token, subscription_id)
        
        if success:
            success_text = "✅ <b>Unsubscribed Successfully</b>\n\n"
            success_text += f"Subscription <code>{subscription_id}</code> has been removed.\n"
            success_text += "You will no longer receive notifications for this product."
            
            await callback.message.edit_text(success_text)
        else:
            await callback.message.edit_text("❌ Failed to unsubscribe. The subscription might not exist or already be removed.")
    
    except Exception as e:
        logger.error(f"Error confirming unsubscribe: {e}")
        await callback.message.edit_text("❌ An error occurred while unsubscribing.")
    
    await callback.answer()


@router.callback_query(lambda c: c.data == "cancel_unsubscribe")
async def cancel_unsubscribe(callback: types.CallbackQuery) -> None:
    """Handle unsubscribe cancellation."""
    await callback.message.edit_text("❌ Unsubscribe cancelled.")
    await callback.answer()
