# backend/app/config.py
import os
from functools import lru_cache
from typing import Any, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    # Database
    database_url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/smartcatcher",
        description="Database URL",
    )

    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379",
        description="Redis URL for Celery broker and cache",
    )

    # JWT
    jwt_secret_key: str = Field(
        default="supersecretjwtkey",
        description="Secret key for JWT tokens",
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_access_token_expire_minutes: int = Field(
        default=30, description="Access token expiration in minutes"
    )
    jwt_refresh_token_expire_days: int = Field(
        default=7, description="Refresh token expiration in days"
    )

    # Telegram Bot
    telegram_bot_token: str = Field(
        default="", description="Telegram bot token"
    )

    # eBay API
    ebay_client_id: str = Field(default="", description="eBay API client ID")
    ebay_client_secret: str = Field(default="", description="eBay API client secret")
    ebay_environment: str = Field(
        default="sandbox", description="eBay environment (sandbox/production)"
    )
    ebay_rate_limit_requests_per_day: int = Field(
        default=5000, description="eBay API rate limit per day"
    )

    # Etsy API
    etsy_api_key: str = Field(default="", description="Etsy API key")
    etsy_rate_limit_requests_per_second: int = Field(
        default=10, description="Etsy API rate limit per second"
    )

    # Scraper settings
    scraper_user_agent: str = Field(
        default="SmartCatcher/1.0 (+https://example.com/bot)",
        description="User agent for web scraping",
    )
    scraper_request_delay: float = Field(
        default=1.0, description="Delay between scraper requests in seconds"
    )
    scraper_retry_attempts: int = Field(
        default=3, description="Number of retry attempts for failed requests"
    )
    scraper_timeout: int = Field(
        default=30, description="Request timeout in seconds"
    )

    # Celery Beat
    price_check_interval_minutes: int = Field(
        default=60, description="Price check interval in minutes"
    )

    # Debug and logging
    debug: bool = Field(default=True, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")

    # Environment
    environment: str = Field(default="development", description="Environment name")

    model_config = SettingsConfigDict(env_file = os.getenv("ENV_FILE", ".env"), case_sensitive=False)

    @field_validator("database_url", mode="before")
    def validate_database_url(cls, v: str) -> str:
        """Validate database URL."""
        if not v.startswith(("postgresql://", "postgresql+asyncpg://")):
            raise ValueError("Database URL must be a PostgreSQL connection string")
        return v

    @field_validator("jwt_secret_key")
    def validate_jwt_secret_key(cls, v: str) -> str:
        """Validate JWT secret key."""
        if len(v) < 32:
            raise ValueError("JWT secret key must be at least 32 characters long")
        return v

    @field_validator("environment")
    def validate_environment(cls, v: str) -> str:
        """Validate environment."""
        allowed_environments = ["development", "staging", "production"]
        if v not in allowed_environments:
            raise ValueError(f"Environment must be one of: {allowed_environments}")
        return v

    @property
    def ebay_base_url(self) -> str:
        """Get eBay API base URL based on environment."""
        if self.ebay_environment == "production":
            return "https://api.ebay.com"
        return "https://api.sandbox.ebay.com"

    @property
    def etsy_base_url(self) -> str:
        """Get Etsy API base URL."""
        return "https://openapi.etsy.com/v3"

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == "production"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
