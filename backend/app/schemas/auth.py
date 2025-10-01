# backend/app/schemas/auth.py

from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserLogin(BaseModel):
    """User login schema."""
    username: EmailStr
    password: str = Field(..., max_length=70)

    @field_validator("password")
    @classmethod
    def validate_password_length(cls, v: str) -> str:
        """Validate password doesn't exceed bcrypt 72-byte limit."""
        if len(v.encode("utf-8")) > 72:
            raise ValueError("Password must be less than 72 bytes when encoded.")
        return v


class UserRegister(BaseModel):
    """User registration schema."""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=70)

    @field_validator("password")
    @classmethod
    def validate_password_length(cls, v: str) -> str:
        """Validate password doesn't exceed bcrypt 72-byte limit."""
        if len(v.encode("utf-8")) > 72:
            raise ValueError("Password must be less than 72 bytes when encoded.")
        return v


class Token(BaseModel):
    """Token schema."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token data schema."""
    username: Optional[str] = None
    user_id: Optional[int] = None

class RefreshTokenRequest(BaseModel):
    """Refresh token request schema."""
    refresh_token: str
