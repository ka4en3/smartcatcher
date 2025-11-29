# bot/handlers/start.py

import logging
from typing import Any

from aiogram import Router, types
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from utils.api_client import APIClient

logger = logging.getLogger(__name__)
router = Router()


class AuthStates(StatesGroup):
    """Authentication states."""
    waiting_for_credentials = State()
    waiting_for_registration = State()


@router.message(CommandStart())
async def start_command(
        message: types.Message,
        state: FSMContext,
        api_client: APIClient,
        token_storage: Any,
        is_authenticated: bool = False
) -> None:
    """Handle /start command."""

    if is_authenticated:
        welcome_text = "🎉 <b>Welcome back!</b>\n\n"
        welcome_text += "Your account is already linked. You can:\n"
        welcome_text += "• /subscribe - Subscribe to product price changes\n"
        welcome_text += "• /list - View your active subscriptions\n"
        welcome_text += "• /help - Get help with commands"

        await message.answer(welcome_text)
    else:
        welcome_text = "🤖 <b>Welcome to SmartCatcher!</b>\n\n"
        welcome_text += "I help you track product prices and get notified when they drop.\n\n"
        welcome_text += "To get started, you need to link your account:"

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔗 Link Existing Account", callback_data="link_account")],
            [InlineKeyboardButton(text="📝 Create New Account", callback_data="register_account")],
        ])

        await message.answer(welcome_text, reply_markup=keyboard)


@router.callback_query(lambda c: c.data == "link_account")
async def link_account_callback(callback: types.CallbackQuery, state: FSMContext) -> None:
    """Handle link account callback."""
    text = "🔗 <b>Link Existing Account</b>\n\n"
    text += "Please send your credentials in the following format:\n"
    text += "<code>email@example.com password</code>\n\n"
    text += "⚠️ <b>Important:</b> Send credentials in ONE message. They will be deleted immediately for security.\n\n"
    text += "💡 Tip: Use /cancel to abort"

    await callback.message.edit_text(text)
    await state.set_state(AuthStates.waiting_for_credentials)
    await callback.answer()


@router.callback_query(lambda c: c.data == "register_account")
async def register_account_callback(callback: types.CallbackQuery, state: FSMContext) -> None:
    """Handle register account callback."""
    text = "📝 <b>Create New Account</b>\n\n"
    text += "Please send your registration details in the following format:\n"
    text += "<code>email@example.com password</code>\n\n"
    text += "Choose a strong password (at least 8 characters).\n\n"
    text += "💡 Tip: Use /cancel to abort"

    await callback.message.edit_text(text)
    await state.set_state(AuthStates.waiting_for_registration)
    await callback.answer()


@router.message(Command("cancel"))
async def cancel_handler(message: types.Message, state: FSMContext) -> None:
    """Cancel current operation."""
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Nothing to cancel.")
        return

    await state.clear()
    await message.answer("❌ Operation cancelled. Use /start to begin again.")


@router.message(AuthStates.waiting_for_credentials)
async def process_login_credentials(
        message: types.Message,
        state: FSMContext,
        api_client: APIClient,
        token_storage: Any
) -> None:
    """Process login credentials."""
    # Immediately try to delete the message
    message_to_delete = message.message_id

    try:
        # Parse credentials
        credentials = message.text.strip().split(maxsplit=1)
        if len(credentials) != 2:
            await message.answer("❌ Invalid format. Use: <code>email@example.com password</code>")
            return

        email, password = credentials
        user_id = message.from_user.id
        username = message.from_user.username

        # Try to delete message with credentials
        try:
            await message.delete()
        except Exception as e:
            logger.warning(f"Could not delete credentials message: {e}")

        # Show processing message
        processing_msg = await message.answer("⏳ Logging in...")

        # Try to login
        login_result = await api_client.login(email, password)
        if not login_result:
            await processing_msg.edit_text("❌ Invalid email or password. Please try again or use /cancel.")
            return

        # Save tokens
        token_storage.save_tokens(
            user_id,
            login_result["access_token"],
            login_result.get("refresh_token", "")
        )

        # Link Telegram account
        link_result = await api_client.link_telegram_account(
            login_result["access_token"], user_id, username
        )

        if link_result:
            success_text = "✅ <b>Account linked successfully!</b>\n\n"
            success_text += f"Email: <code>{email}</code>\n\n"
            success_text += "You can now:\n"
            success_text += "• /subscribe - Subscribe to product price changes\n"
            success_text += "• /list - View your active subscriptions\n"
            success_text += "• /help - Get help with commands"

            await processing_msg.edit_text(success_text)
            await state.clear()
        else:
            await processing_msg.edit_text(
                "❌ Login successful but failed to link Telegram account. Please try /start again.")

    except Exception as e:
        logger.error(f"Error processing login credentials: {e}")
        await message.answer("❌ An error occurred. Please try again.")


@router.message(AuthStates.waiting_for_registration)
async def process_registration(
        message: types.Message,
        state: FSMContext,
        api_client: APIClient,
        token_storage: Any
) -> None:
    """Process registration."""
    try:
        # Parse credentials
        credentials = message.text.strip().split(maxsplit=1)
        if len(credentials) != 2:
            await message.answer("❌ Invalid format. Use: <code>email@example.com password</code>")
            return

        email, password = credentials
        user_id = message.from_user.id
        username = message.from_user.username

        # Try to delete message with credentials
        try:
            await message.delete()
        except Exception as e:
            logger.warning(f"Could not delete credentials message: {e}")

        # Validate password
        if len(password) < 8:
            await message.answer("❌ Password must be at least 8 characters long.")
            return

        processing_msg = await message.answer("⏳ Creating account...")

        # Try to register
        register_result = await api_client.register(email, password)
        if not register_result:
            await processing_msg.edit_text("❌ Registration failed. Email might already be registered.")
            return

        # Login with new account
        login_result = await api_client.login(email, password)
        if not login_result:
            await processing_msg.edit_text(
                "❌ Registration succeeded but login failed. Please use /start to link your account.")
            return

        # Save tokens
        token_storage.save_tokens(
            user_id,
            login_result["access_token"],
            login_result.get("refresh_token", "")
        )

        # Link Telegram account
        link_result = await api_client.link_telegram_account(
            login_result["access_token"], user_id, username
        )

        if link_result:
            success_text = "🎉 <b>Account created and linked successfully!</b>\n\n"
            success_text += f"Email: <code>{email}</code>\n\n"
            success_text += "You can now:\n"
            success_text += "• /subscribe - Subscribe to product price changes\n"
            success_text += "• /list - View your active subscriptions\n"
            success_text += "• /help - Get help with commands"

            await processing_msg.edit_text(success_text)
            await state.clear()
        else:
            await processing_msg.edit_text("❌ Account created but failed to link. Please use /start to link manually.")

    except Exception as e:
        logger.error(f"Error processing registration: {e}")
        await message.answer("❌ An error occurred. Please try again.")


@router.message(Command("help"))
async def help_command(message: types.Message) -> None:
    """Handle /help command."""
    help_text = "🤖 <b>SmartCatcher Bot Commands</b>\n\n"
    help_text += "<b>Account Management:</b>\n"
    help_text += "• /start - Start bot and link account\n"
    help_text += "• /help - Show this help message\n"
    help_text += "• /cancel - Cancel current operation\n\n"
    help_text += "<b>Subscriptions:</b>\n"
    help_text += "• /subscribe <url> - Subscribe to product\n"
    help_text += "• /list - Show your subscriptions\n"
    help_text += "• /unsubscribe <id> - Remove subscription\n\n"
    help_text += "<b>Example:</b>\n"
    help_text += "<code>/subscribe https://www.ebay.com/itm/123456789</code>\n\n"
    help_text += "💡 <i>You'll receive notifications when prices drop below your threshold!</i>"

    await message.answer(help_text)