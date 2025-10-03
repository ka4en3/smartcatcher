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
