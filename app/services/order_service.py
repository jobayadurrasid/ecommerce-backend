import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Tuple
from app.core.exceptions import NotFoundError, BadRequestError, ForbiddenError
from app.models.order import Order, OrderStatus
from app.models.user import User, UserRole
from app.repositories.order_repository import OrderRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.order import OrderCreate, OrderResponse, OrderItemResponse


class OrderService:
    TAX_RATE = Decimal("0.05")  # 5% tax

    def __init__(self):
        self.order_repo = OrderRepository()
        self.product_repo = ProductRepository()

    def create_order(self, user_id: uuid.UUID, payload: OrderCreate) -> OrderResponse:
        subtotal = Decimal("0.00")
        items_data = []

        for item_in in payload.items:
            product = self.product_repo.get_by_id(item_in.product_id)
            if not product:
                raise NotFoundError(f"Product '{item_in.product_id}' not found.")

            if not product.is_active:
                raise BadRequestError(f"Product '{product.name}' is currently unavailable.")

            if product.stock < item_in.quantity:
                raise BadRequestError(
                    f"Insufficient stock for '{product.name}'. Available: {product.stock}, Requested: {item_in.quantity}"
                )

            item_subtotal = (product.price * item_in.quantity).quantize(Decimal("0.01"))
            subtotal += item_subtotal

            items_data.append({
                "product_id": product.id,
                "quantity": item_in.quantity,
                "unit_price": product.price,
                "subtotal": item_subtotal,
            })

        tax = (subtotal * self.TAX_RATE).quantize(Decimal("0.01"))
        total_amount = subtotal + tax

        # Format: ORD-YYYYMMDD-8CHARHEX
        timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        unique_suffix = uuid.uuid4().hex[:8].upper()
        order_number = f"ORD-{timestamp_str}-{unique_suffix}"

        order_data = {
            "user_id": user_id,
            "order_number": order_number,
            "status": OrderStatus.PENDING,
            "subtotal": subtotal,
            "tax": tax,
            "total_amount": total_amount,
            "shipping_address": payload.shipping_address,
        }

        order = self.order_repo.create(order_data, items_data)
        return self._to_order_response(order)

    def get_order_by_id(self, order_id: str | uuid.UUID, current_user: User) -> OrderResponse:
        order = self.order_repo.get_by_id(order_id)
        if not order:
            raise NotFoundError("Order not found")

        if current_user.role != UserRole.ADMIN and order.user_id != current_user.id:
            raise ForbiddenError("You do not have permission to view this order")

        return self._to_order_response(order)

    def list_orders(self, current_user: User, page: int = 1, page_size: int = 20) -> Tuple[List[OrderResponse], int]:
        if current_user.role == UserRole.ADMIN:
            orders, total = self.order_repo.list_all(page=page, page_size=page_size)
        else:
            orders, total = self.order_repo.list_by_user(current_user.id, page=page, page_size=page_size)

        return [self._to_order_response(o) for o in orders], total

    def cancel_order(self, order_id: str | uuid.UUID, current_user: User) -> OrderResponse:
        order = self.order_repo.get_by_id(order_id)
        if not order:
            raise NotFoundError("Order not found")

        if current_user.role != UserRole.ADMIN and order.user_id != current_user.id:
            raise ForbiddenError("You do not have permission to cancel this order")

        if order.status != OrderStatus.PENDING:
            raise BadRequestError(f"Cannot cancel order in '{order.status.value}' state.")

        updated = self.order_repo.update_status(order, OrderStatus.CANCELLED)
        return self._to_order_response(updated)

    def _to_order_response(self, order: Order) -> OrderResponse:
        items = [
            OrderItemResponse(
                id=item.id,
                product_id=item.product_id,
                quantity=item.quantity,
                unit_price=item.unit_price,
                subtotal=item.subtotal,
            )
            for item in order.items
        ]
        return OrderResponse(
            id=order.id,
            user_id=order.user_id,
            order_number=order.order_number,
            status=order.status,
            subtotal=order.subtotal,
            tax=order.tax,
            total_amount=order.total_amount,
            shipping_address=order.shipping_address,
            created_at=order.created_at,
            items=items,
        )
