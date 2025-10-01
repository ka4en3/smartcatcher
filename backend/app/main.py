# backend/app/main.py

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import auth, products, subscriptions, users
from app.config import get_settings
from app.core.exceptions import SmartCatcherException
from app.database import create_tables


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    # Startup
    await create_tables()
    yield
    # Shutdown
    pass


# Initialize FastAPI app
app = FastAPI(
    title="SmartCatcher API",
    description="Discount & Coupon Aggregator Bot API",
    version="1.0.0",
    lifespan=lifespan,
)

# Get settings
settings = get_settings()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(SmartCatcherException)
async def smartcatcher_exception_handler(
    request, exc: SmartCatcherException
) -> JSONResponse:
    """Handle custom SmartCatcher exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "error_code": exc.error_code},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


# Health check endpoint
@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "version": "1.0.0"}


# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(products.router, prefix="/products", tags=["Products"])
app.include_router(subscriptions.router, prefix="/subscriptions", tags=["Subscriptions"])


# Root endpoint
@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint with API information."""
    return {
        "message": "SmartCatcher API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
    }
