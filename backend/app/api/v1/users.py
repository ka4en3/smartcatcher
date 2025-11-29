# backend/app/api/v1/users.py
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.database import get_session
from app.models.user import User
from app.schemas.user import UserRead, UserUpdate
from app.services.user import UserService

from app.core.exceptions import UserNotFoundException

router = APIRouter()


@router.get("/me", response_model=UserRead)
async def get_current_user_profile(
        current_user: User = Depends(get_current_active_user),
) -> UserRead:
    """Get current user profile."""
    return UserRead.model_validate(current_user, from_attributes=True)


@router.patch("/me", response_model=UserRead)
async def update_current_user_profile(
        user_update: UserUpdate,
        current_user: User = Depends(get_current_active_user),
        session: AsyncSession = Depends(get_session),
) -> UserRead:
    """Update current user profile."""
    user_service = UserService(session)

    try:
        updated_user = await user_service.update(current_user.id, user_update)
    except UserNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
    return UserRead.model_validate(updated_user, from_attributes=True)


@router.get("/by-telegram/{telegram_user_id}", response_model=UserRead)
async def get_user_by_telegram_id(
        telegram_user_id: int,
        session: AsyncSession = Depends(get_session),
) -> UserRead:
    """
    Get user by Telegram user ID.

    This endpoint is used by the Telegram bot to check if a user is already linked.
    It does not require authentication to allow the bot to verify user status.

    Note: In production, you should secure this endpoint with API key authentication
    to prevent unauthorized access.
    """
    user_service = UserService(session)

    user = await user_service.get_by_telegram_user_id(telegram_user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User with this Telegram ID not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    return UserRead.model_validate(user, from_attributes=True)
