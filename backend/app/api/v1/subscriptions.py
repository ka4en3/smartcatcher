# backend/app/api/v1/subscriptions.py

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.database import get_session
from app.models.user import User
from app.schemas.subscription import SubscriptionCreate, SubscriptionRead, SubscriptionUpdate
from app.services.subscription import SubscriptionService

from app.core.exceptions import ValidationException, SubscriptionNotFoundException

router = APIRouter()


@router.get("", response_model=list[SubscriptionRead])
async def list_subscriptions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    active_only: bool = Query(True),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> list[SubscriptionRead]:
    """List user subscriptions."""
    subscription_service = SubscriptionService(session)
    subscriptions = await subscription_service.list_user_subscriptions(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        active_only=active_only,
    )
    return [SubscriptionRead.model_validate(sub, from_attributes=True) for sub in subscriptions]


@router.post("", response_model=SubscriptionRead, status_code=status.HTTP_201_CREATED)
async def create_subscription(
    subscription_data: SubscriptionCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> SubscriptionRead:
    """Create new subscription."""
    subscription_service = SubscriptionService(session)
    
    try:
        subscription = await subscription_service.create_subscription(
            user_id=current_user.id,
            subscription_data=subscription_data,
        )
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )

    return SubscriptionRead.model_validate(subscription, from_attributes=True)


@router.get("/{subscription_id}", response_model=SubscriptionRead)
async def get_subscription(
    subscription_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> SubscriptionRead:
    """Get subscription by ID."""
    subscription_service = SubscriptionService(session)
    subscription = await subscription_service.get_by_id(subscription_id)
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found",
        )

    if not subscription.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription is not active",
        )
    
    # Check if subscription belongs to current user
    if subscription.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this subscription",
        )
    
    return SubscriptionRead.model_validate(subscription, from_attributes=True)


@router.patch("/{subscription_id}", response_model=SubscriptionRead)
async def update_subscription(
    subscription_id: int,
    subscription_update: SubscriptionUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> SubscriptionRead:
    """Update subscription."""
    subscription_service = SubscriptionService(session)
    subscription = await subscription_service.get_by_id(subscription_id)
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found",
        )
    
    # Check if subscription belongs to current user
    if subscription.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this subscription",
        )
    try:
        updated_subscription = await subscription_service.update(
            subscription_id, subscription_update
        )
    except SubscriptionNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
    return SubscriptionRead.model_validate(updated_subscription, from_attributes=True)


@router.delete("/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subscription(
    subscription_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """Delete subscription."""
    subscription_service = SubscriptionService(session)
    subscription = await subscription_service.get_by_id(subscription_id)
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found",
        )
    
    # Check if subscription belongs to current user
    if subscription.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this subscription",
        )
    
    await subscription_service.delete(subscription_id)
