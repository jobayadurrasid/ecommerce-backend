import uuid
from fastapi import APIRouter, Depends, Query, status
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.common import PaginatedData
from app.schemas.order import OrderCreate, OrderResponse
from app.services.order_service import OrderService

router = APIRouter(
    prefix="/orders",
    tags=["Orders"],
)


@router.post(
    "/",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_order(
    payload: OrderCreate,
    current_user: User = Depends(get_current_user),
):
    service = OrderService()
    return service.create_order(current_user.id, payload)


@router.get(
    "/",
    response_model=PaginatedData[OrderResponse],
    status_code=status.HTTP_200_OK,
)
def list_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
):
    service = OrderService()
    items, total = service.list_orders(current_user, page=page, page_size=page_size)
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    return PaginatedData[OrderResponse](
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
    status_code=status.HTTP_200_OK,
)
def get_order(
    order_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
):
    service = OrderService()
    return service.get_order_by_id(order_id, current_user)


@router.post(
    "/{order_id}/cancel",
    response_model=OrderResponse,
    status_code=status.HTTP_200_OK,
)
def cancel_order(
    order_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
):
    service = OrderService()
    return service.cancel_order(order_id, current_user)
