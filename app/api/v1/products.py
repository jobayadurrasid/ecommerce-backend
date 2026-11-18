import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from app.core.dependencies import require_admin
from app.models.user import User
from app.schemas.common import PaginatedData
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse
from app.services.product_service import ProductService

router = APIRouter(
    prefix="/products",
    tags=["Products"],
)


@router.get(
    "/",
    response_model=PaginatedData[ProductResponse],
    status_code=status.HTTP_200_OK,
)
def get_products(
    category_id: Optional[uuid.UUID] = Query(None, description="Filter by category"),
    include_subcategories: bool = Query(True, description="Include products in descendant subcategories"),
    is_active: Optional[bool] = Query(True, description="Filter active status"),
    search: Optional[str] = Query(None, description="Search product name or description"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    service = ProductService()
    items, total = service.list_products(
        category_id=category_id,
        include_subcategories=include_subcategories,
        is_active=is_active,
        search=search,
        page=page,
        page_size=page_size,
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    return PaginatedData[ProductResponse](
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    status_code=status.HTTP_200_OK,
)
def get_product(product_id: uuid.UUID):
    service = ProductService()
    return service.get_product_by_id(product_id)


@router.post(
    "/",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_product(
    payload: ProductCreate,
    _: User = Depends(require_admin),
):
    service = ProductService()
    return service.create_product(payload)


@router.put(
    "/{product_id}",
    response_model=ProductResponse,
    status_code=status.HTTP_200_OK,
)
def update_product(
    product_id: uuid.UUID,
    payload: ProductUpdate,
    _: User = Depends(require_admin),
):
    service = ProductService()
    return service.update_product(product_id, payload)


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_product(
    product_id: uuid.UUID,
    _: User = Depends(require_admin),
):
    service = ProductService()
    service.delete_product(product_id)
    return None
