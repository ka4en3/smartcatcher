# backend/app/api/v1/products.py

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin_user, get_current_active_user
from app.database import get_session
from app.models.user import User
from app.schemas.product import ProductCreate, ProductRead, ProductUpdate, PriceHistoryRead, ProductByUrl
from app.services.product import ProductService

from app.core.exceptions import ValidationException, ProductNotFoundException

router = APIRouter()


@router.get("", response_model=list[ProductRead])
async def list_products(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=1000),
        search: Optional[str] = Query(None),
        brand: Optional[str] = Query(None),
        store: Optional[str] = Query(None),
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_current_active_user),
) -> list[ProductRead]:
    """List products with optional filtering."""
    product_service = ProductService(session)
    products = await product_service.list_products(
        skip=skip,
        limit=limit,
        search=search,
        brand=brand,
        store=store,
    )
    return [ProductRead.model_validate(product, from_attributes=True) for product in products]


@router.get("/{product_id}", response_model=ProductRead)
async def get_product(
        product_id: int,
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_current_active_user),
) -> ProductRead:
    """Get product by ID."""
    product_service = ProductService(session)
    product = await product_service.get_by_id(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    return ProductRead.model_validate(product, from_attributes=True)


@router.post("", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
async def create_product(
        product_data: ProductCreate,
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_current_admin_user),
) -> ProductRead:
    """Create new product (admin only)."""
    product_service = ProductService(session)
    try:
        product = await product_service.create(product_data)
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
    return ProductRead.model_validate(product, from_attributes=True)


@router.post("/by-url", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
async def create_or_get_product_by_url(
        payload: ProductByUrl,
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_current_active_user),
) -> ProductRead:
    """Create product by URL, if it doesn't exist. Otherwise, return existing product."""
    product_service = ProductService(session)
    normalized_url = str(payload.url).strip().lower()

    # Check if product with this URL already exists
    existing_product = await product_service.get_by_url(normalized_url)
    if existing_product:
        return ProductRead.model_validate(existing_product, from_attributes=True)

    # Create product
    try:
        product = await product_service.create_by_url(normalized_url)
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
    return ProductRead.model_validate(product, from_attributes=True)


@router.patch("/{product_id}", response_model=ProductRead)
async def update_product(
        product_id: int,
        product_update: ProductUpdate,
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_current_admin_user),
) -> ProductRead:
    """Update product (admin only)."""
    product_service = ProductService(session)

    existing_product = await product_service.get_by_id(product_id)
    if not existing_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    try:
        updated_product = await product_service.update(product_id, product_update)
    except ProductNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
    return ProductRead.model_validate(updated_product, from_attributes=True)


@router.get("/{product_id}/price-history", response_model=list[PriceHistoryRead])
async def get_product_price_history(
        product_id: int,
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=1000),
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_current_active_user),
) -> list[PriceHistoryRead]:
    """Get product price history."""
    product_service = ProductService(session)

    # Check if product exists
    product = await product_service.get_by_id(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    price_history = await product_service.get_price_history(product_id, skip, limit)
    return [PriceHistoryRead.model_validate(entry, from_attributes=True) for entry in price_history]
