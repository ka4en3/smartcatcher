# backend/app/api/v1/auth.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.schemas.auth import Token, UserLogin, UserRegister, RefreshTokenRequest
from app.schemas.user import UserRead
from app.services.auth import AuthService

router = APIRouter()


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(
        user_data: UserRegister,
        session: AsyncSession = Depends(get_session),
) -> UserRead:
    """Register new user."""
    auth_service = AuthService(session)

    # Check if user already exists
    existing_user = await auth_service.get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    user = await auth_service.create_user(user_data.email, user_data.password)
    return UserRead.model_validate(user, from_attributes=True)


@router.post("/login", response_model=Token)
async def login(
        user_credentials: UserLogin,
        session: AsyncSession = Depends(get_session),
) -> Token:
    """Login user and return tokens."""
    auth_service = AuthService(session)

    user = await auth_service.authenticate_user(
        user_credentials.username, user_credentials.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )

    access_token = auth_service.create_access_token(data={"sub": str(user.id)})
    refresh_token = auth_service.create_refresh_token(data={"sub": str(user.id)})

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
        refresh_data: RefreshTokenRequest,
        session: AsyncSession = Depends(get_session),
) -> Token:
    """Refresh access token."""
    auth_service = AuthService(session)

    try:
        new_access_token, new_refresh_token = await auth_service.refresh_tokens(refresh_data.refresh_token)

        return Token(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        ) from e
