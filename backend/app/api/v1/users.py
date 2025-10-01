# backend/app/api/v1/users.py

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.database import get_session
from app.models.user import User
from app.schemas.user import UserRead, UserUpdate
from app.services.user import UserService

router = APIRouter()


@router.get("/me", response_model=UserRead)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user),
) -> UserRead:
    """Get current user profile."""
    return UserRead.from_orm(current_user)


@router.patch("/me", response_model=UserRead)
async def update_current_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> UserRead:
    """Update current user profile."""
    user_service = UserService(session)
    updated_user = await user_service.update(current_user.id, user_update)
    return UserRead.from_orm(updated_user)
