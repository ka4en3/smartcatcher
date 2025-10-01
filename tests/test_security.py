"""Unit tests for security functions."""
import pytest
from datetime import datetime, timedelta
from jose import jwt

from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token
)
from app.config import get_settings


class TestPasswordHashing:
    """Test password hashing and verification."""

    def test_password_hashing(self):
        """Test password hashing works correctly."""
        password = "testpassword123"
        hashed = get_password_hash(password)

        assert hashed != password
        assert len(hashed) > 50  # bcrypt_sha256 produces long hashes
        assert verify_password(password, hashed)

    def test_wrong_password_verification(self):
        """Test wrong password verification fails."""
        password = "correct_password"
        wrong_password = "wrong_password"
        hashed = get_password_hash(password)

        assert not verify_password(wrong_password, hashed)

    def test_empty_password(self):
        """Test empty password handling."""
        empty_password = ""
        hashed = get_password_hash(empty_password)

        assert verify_password(empty_password, hashed)
        assert not verify_password("not_empty", hashed)


class TestJWTTokens:
    """Test JWT token creation and decoding."""

    def test_create_access_token(self):
        """Test access token creation."""
        user_id = 123
        token = create_access_token(user_id)

        assert isinstance(token, str)
        assert len(token) > 50

        # Decode and verify
        payload = decode_token(token)
        assert payload["sub"] == user_id
        assert payload["type"] == "access"
        assert "exp" in payload

    def test_create_refresh_token(self):
        """Test refresh token creation."""
        user_id = 456
        token = create_refresh_token(user_id)

        payload = decode_token(token)
        assert payload["sub"] == user_id
        assert payload["type"] == "refresh"

    def test_token_expiration(self):
        """Test token expiration handling."""
        user_id = 789
        # Create token that expires in 1 second
        expires_delta = timedelta(seconds=1)
        token = create_access_token(user_id, expires_delta)

        # Should work immediately
        payload = decode_token(token)
        assert payload["sub"] == user_id

        # Mock expired token by manually creating one
        settings = get_settings()
        expired_payload = {
            "sub": user_id,
            "exp": datetime.utcnow() - timedelta(minutes=1),
            "type": "access"
        }
        expired_token = jwt.encode(
            expired_payload,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm
        )

        with pytest.raises(Exception):  # Should raise JWT exception
            decode_token(expired_token)

    def test_invalid_token(self):
        """Test invalid token handling."""
        invalid_token = "invalid.token.here"

        with pytest.raises(Exception):
            decode_token(invalid_token)

    def test_token_with_string_user_id(self):
        """Test token creation with string user_id converts to int."""
        user_id = "123"  # String input
        token = create_access_token(user_id)

        payload = decode_token(token)
        assert payload["sub"] == 123  # Should be converted to int
        assert isinstance(payload["sub"], int)
