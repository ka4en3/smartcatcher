# bot/handlers/subscription.py

import logging
import re

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
async def subscribe_command(
    message: types.Message,
    state: FSMContext,
    api_client: APIClient,
    access_token: str = None,
    is_authenticated: bool = False
) -> None:
    """Handle /subscribe command."""
    if not is_authenticated or not access_token:
        await message.answer("❌ Please link your account first using /start")
        return

    # Extract URL from command
    command_parts = message.text.split(maxsplit=1)
    if len(command_parts) < 2:
        help_text = "🔗 <b>Subscribe to Product</b>\n\n"
        help_text += "Please provide a product URL:\n"
        help_text += "<code>/subscribe https://webscraper.io/test-sites/e-commerce/scroll/product/70</code>\n\n"
        help_text += "<b>Supported sites:</b>\n"
        help_text += "• eBay\n"
        help_text += "• Etsy\n"
        help_text += "• WebScraper.io test sites\n"
        help_text += "• Demo URLs"

        await message.answer(help_text)
        return

    product_url = command_parts[1].strip()

    # Validate URL format
    url_pattern = r'https?://[^\s]+'
    if (not re.match(url_pattern, product_url)) and (not "demo-server" in product_url):
        await message.answer("❌ Invalid URL format. Please provide a valid HTTP/HTTPS URL.")
        return

    # Store URL and token in state
    await state.update_data(product_url=product_url, access_token=access_token)

    # Ask for price threshold
    threshold_text = "💰 <b>Set Price Threshold</b>\n\n"
    threshold_text += f"Product URL:\n<code>{product_url[:80]}</code>\n\n"
    threshold_text += "Please set a price threshold. You'll be notified when the price drops below this amount.\n\n"
    threshold_text += "Enter threshold amount (e.g., <code>100</code> or <code>99.99</code>):"

    await message.answer(threshold_text)
    await state.set_state(SubscriptionStates.waiting_for_threshold)


@router.message(SubscriptionStates.waiting_for_threshold)
async def process_threshold(
    message: types.Message,
    state: FSMContext,
    api_client: APIClient
) -> None:
    """Process price threshold."""
    try:
        # Get stored data
        data = await state.get_data()
        product_url = data.get("product_url")
        access_token = data.get("access_token")

        if not product_url or not access_token:
            await message.answer("❌ Session expired. Please start over with /subscribe")
            await state.clear()
            return

        # Parse threshold
        threshold_text = message.text.strip()

        # Remove currency symbols and commas
        threshold_text = re.sub(r'[^\d.]', '', threshold_text)

        try:
            threshold = float(threshold_text)
        except ValueError:
            await message.answer("❌ Invalid number format. Please enter a valid amount (e.g., 100 or 99.99).")
            return

        if threshold <= 0:
            await message.answer("❌ Threshold must be greater than 0. Please try again.")
            return

        # Create subscription
        subscription_data = {
            "product_url": product_url,
            "subscription_type": "product",
            "price_threshold": threshold
        }

        loading_msg = await message.answer("⏳ Creating subscription...")

        try:
            subscription = await api_client.create_subscription(access_token, subscription_data)

            if subscription:
                success_text = "✅ <b>Subscription Created!</b>\n\n"
                success_text += f"🔗 URL:\n<code>{product_url[:60]}</code>\n\n"
                success_text += f"💰 Threshold: <code>${threshold:.2f}</code>\n"
                success_text += f"🆔 Subscription ID: <code>{subscription['id']}</code>\n\n"
                success_text += "🔔 You'll receive notifications when the price drops below your threshold!"

                await loading_msg.edit_text(success_text)
                await state.clear()
            else:
                await loading_msg.edit_text(
                    "❌ Failed to create subscription. The product might not be found or already tracked.")
                await state.clear()

        except Exception as e:
            logger.error(f"Error creating subscription: {e}")
            error_text = "❌ Failed to create subscription.\n\n"
            if "not found" in str(e).lower():
                error_text += "The product URL might be invalid or the product is not available."
            else:
                error_text += "Please try again later or contact support."

            await loading_msg.edit_text(error_text)
            await state.clear()

    except Exception as e:
        logger.error(f"Error processing threshold: {e}")
        await message.answer("❌ An error occurred. Please try again.")
        await state.clear()


@router.message(Command("list"))
async def list_subscriptions(
    message: types.Message,
    api_client: APIClient,
    access_token: str = None,
    is_authenticated: bool = False
) -> None:
    """Handle /list command."""
    if not is_authenticated or not access_token:
        await message.answer("❌ Please link your account first using /start")
        return

    try:
        subscriptions = await api_client.get_user_subscriptions(access_token)

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
                    product = await api_client.get_product(access_token, product_id)
                    if product:
                        title = product.get("title", "Unknown Product")[:40]
                        current_price = product.get("current_price")
                        currency = product.get("currency", "USD")

                        list_text += f"<code>{title}</code>\n"
                        if current_price is not None:
                            list_text += f"   💰 Current: ${current_price:.2f} {currency}\n"
                        if threshold is not None:
                            list_text += f"   🎯 Threshold: ${threshold:.2f}\n"
                        list_text += f"   🆔 ID: <code>{subscription_id}</code>\n\n"
                    else:
                        list_text += f"Product ID: {product_id}\n"
                        if threshold is not None:
                            list_text += f"   🎯 Threshold: ${threshold:.2f}\n"
                        list_text += f"   🆔 ID: <code>{subscription_id}</code>\n\n"
                except Exception as e:
                    logger.warning(f"Failed to fetch product {product_id}: {e}")
                    list_text += f"Product ID: {product_id}\n"
                    if threshold is not None:
                        list_text += f"   🎯 Threshold: ${threshold:.2f}\n"
                    list_text += f"   🆔 ID: <code>{subscription_id}</code>\n\n"
            else:
                list_text += f"Subscription ID: {subscription_id}\n"
                if threshold is not None:
                    list_text += f"   🎯 Threshold: ${threshold:.2f}\n\n"

        list_text += "💡 Use <code>/unsubscribe [ID]</code> to remove a subscription."

        # Split message if too long (Telegram limit is 4096 characters)
        if len(list_text) > 4000:
            parts = [list_text[i:i + 4000] for i in range(0, len(list_text), 4000)]
            for part in parts:
                await message.answer(part)
        else:
            await message.answer(list_text)

    except Exception as e:
        logger.error(f"Error listing subscriptions: {e}")
        await message.answer("❌ Failed to get subscriptions. Please try again later.")


@router.message(Command("unsubscribe"))
async def unsubscribe_command(
    message: types.Message,
    api_client: APIClient,
    access_token: str = None,
    is_authenticated: bool = False
) -> None:
    """Handle /unsubscribe command."""
    if not is_authenticated or not access_token:
        await message.answer("❌ Please link your account first using /start")
        return

    # Extract subscription ID from command
    command_parts = message.text.split(maxsplit=1)
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
async def confirm_unsubscribe(
    callback: types.CallbackQuery,
    api_client: APIClient,
    access_token: str = None,
    is_authenticated: bool = False
) -> None:
    """Handle unsubscribe confirmation."""
    if not is_authenticated or not access_token:
        await callback.message.edit_text("❌ Authentication lost. Please start over with /start")
        await callback.answer()
        return

    try:
        subscription_id = int(callback.data.split("_")[1])

        # Delete subscription
        success = await api_client.delete_subscription(access_token, subscription_id)

        if success:
            success_text = "✅ <b>Unsubscribed Successfully</b>\n\n"
            success_text += f"Subscription <code>{subscription_id}</code> has been removed.\n"
            success_text += "You will no longer receive notifications for this product."

            await callback.message.edit_text(success_text)
        else:
            await callback.message.edit_text(
                "❌ Failed to unsubscribe. The subscription might not exist or already be removed.")

    except Exception as e:
        logger.error(f"Error confirming unsubscribe: {e}")
        await callback.message.edit_text("❌ An error occurred while unsubscribing.")

    await callback.answer()


@router.callback_query(lambda c: c.data == "cancel_unsubscribe")
async def cancel_unsubscribe(callback: types.CallbackQuery) -> None:
    """Handle unsubscribe cancellation."""
    await callback.message.edit_text("❌ Unsubscribe cancelled.")
    await callback.answer()