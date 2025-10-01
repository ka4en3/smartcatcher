# backend/app/core/exceptions.py

from typing import Optional


class SmartCatcherException(Exception):
    """Base SmartCatcher exception."""

    def __init__(
        self,
        detail: str,
        status_code: int = 500,
        error_code: Optional[str] = None,
    ):
        self.detail = detail
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(detail)


class UserNotFoundException(SmartCatcherException):
    """User not found exception."""

    def __init__(self, detail: str = "User not found"):
        super().__init__(detail=detail, status_code=404, error_code="USER_NOT_FOUND")


class ProductNotFoundException(SmartCatcherException):
    """Product not found exception."""

    def __init__(self, detail: str = "Product not found"):
        super().__init__(detail=detail, status_code=404, error_code="PRODUCT_NOT_FOUND")


class SubscriptionNotFoundException(SmartCatcherException):
    """Subscription not found exception."""

    def __init__(self, detail: str = "Subscription not found"):
        super().__init__(
            detail=detail, status_code=404, error_code="SUBSCRIPTION_NOT_FOUND"
        )


class ScrapingException(SmartCatcherException):
    """Scraping exception."""

    def __init__(self, detail: str = "Scraping failed"):
        super().__init__(detail=detail, status_code=500, error_code="SCRAPING_ERROR")


class AuthenticationException(SmartCatcherException):
    """Authentication exception."""

    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(
            detail=detail, status_code=401, error_code="AUTHENTICATION_ERROR"
        )


class AuthorizationException(SmartCatcherException):
    """Authorization exception."""

    def __init__(self, detail: str = "Not authorized"):
        super().__init__(detail=detail, status_code=403, error_code="AUTHORIZATION_ERROR")


class ValidationException(SmartCatcherException):
    """Validation exception."""

    def __init__(self, detail: str = "Validation failed"):
        super().__init__(detail=detail, status_code=400, error_code="VALIDATION_ERROR")


class ExternalAPIException(SmartCatcherException):
    """External API exception."""

    def __init__(self, detail: str = "External API error", service_name: str = ""):
        super().__init__(
            detail=f"{service_name}: {detail}" if service_name else detail,
            status_code=502,
            error_code="EXTERNAL_API_ERROR",
        )
