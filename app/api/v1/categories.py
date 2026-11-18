import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from app.core.dependencies import require_admin
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse
from app.schemas.product import ProductResponse
from app.services.product_service import ProductService

router = APIRouter(
    prefix="/categories",
    tags=["Categories"],
)


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
)
def get_categories():
    service = ProductService()
    return service.list_categories()


@router.get(
    "/{category_id}",
    response_model=CategoryResponse,
    status_code=status.HTTP_200_OK,
)
def get_category(category_id: uuid.UUID):
    service = ProductService()
    return service.get_category_by_id(category_id)


@router.get(
    "/{category_id}/recommendations",
    response_model=List[ProductResponse],
    status_code=status.HTTP_200_OK,
)
def get_category_recommendations(category_id: uuid.UUID, limit: int = 10):
    service = ProductService()
    products, _ = service.list_products(
        category_id=category_id,
        include_subcategories=True,
        is_active=True,
        page=1,
        page_size=limit,
    )
    return products


@router.post(
    "/",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_category(payload: CategoryCreate, _: User = Depends(require_admin)):
    service = ProductService()
    return service.create_category(payload)


@router.put(
    "/{category_id}",
    response_model=CategoryResponse,
    status_code=status.HTTP_200_OK,
)
def update_category(
    category_id: uuid.UUID,
    payload: CategoryUpdate,
    _: User = Depends(require_admin),
):
    service = ProductService()
    return service.update_category(category_id, payload)


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_category(
    category_id: uuid.UUID,
    _: User = Depends(require_admin),
):
    service = ProductService()
    service.delete_category(category_id)
    return None
