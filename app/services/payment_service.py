import json
import uuid
from decimal import Decimal
from typing import Optional, Dict, Any
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.core.exceptions import NotFoundError, BadRequestError, ForbiddenError
from app.core.logger import logger
from app.database.session import SessionManager
from app.models.order import Order, OrderStatus
from app.models.payment import Payment, PaymentProvider, PaymentStatus
from app.models.user import User, UserRole
from app.repositories.order_repository import OrderRepository
from app.repositories.payment_repository import PaymentRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.payment import CheckoutRequest, CheckoutResponse, PaymentResponse
from app.services.payment.factory import PaymentStrategyFactory


class PaymentService:
    def __init__(self):
        self.payment_repo = PaymentRepository()
        self.order_repo = OrderRepository()
        self.product_repo = ProductRepository()
        self.session_manager = SessionManager()

    def initiate_checkout(self, current_user: User, payload: CheckoutRequest) -> CheckoutResponse:
        order = self.order_repo.get_by_id(payload.order_id)
        if not order:
            raise NotFoundError("Order not found")

        if current_user.role != UserRole.ADMIN and order.user_id != current_user.id:
            raise ForbiddenError("You do not have permission to pay for this order")

        if order.status != OrderStatus.PENDING:
            raise BadRequestError(f"Cannot checkout order with status '{order.status.value}'")

        # Create unique idempotency key for this payment attempt
        idempotency_key = f"pay_{order.id}_{uuid.uuid4().hex[:12]}"

        payment_data = {
            "order_id": order.id,
            "provider": payload.provider,
            "status": PaymentStatus.PENDING,
            "amount": order.total_amount,
            "currency": payload.currency.upper(),
            "idempotency_key": idempotency_key,
        }

        payment = self.payment_repo.create(payment_data)

        # Dispatch to strategy
        strategy = PaymentStrategyFactory.get_strategy(payload.provider)
        session_info = strategy.create_checkout_session(payment, order, return_url=payload.return_url)

        transaction_id = session_info.get("transaction_id")
        if transaction_id:
            self.payment_repo.update_status(
                payment,
                status=PaymentStatus.PENDING,
                transaction_id=transaction_id,
                gateway_response=json.dumps(session_info),
            )

        return CheckoutResponse(
            payment_id=payment.id,
            order_id=order.id,
            provider=payment.provider,
            amount=payment.amount,
            currency=payment.currency,
            status=payment.status,
            checkout_url=session_info.get("checkout_url"),
            client_secret=session_info.get("client_secret"),
            metadata=session_info.get("metadata"),
        )

    def get_payment_by_id(self, payment_id: str | uuid.UUID, current_user: User) -> PaymentResponse:
        payment = self.payment_repo.get_by_id(payment_id)
        if not payment:
            raise NotFoundError("Payment record not found")

        order = self.order_repo.get_by_id(payment.order_id)
        if order and current_user.role != UserRole.ADMIN and order.user_id != current_user.id:
            raise ForbiddenError("You do not have permission to view this payment")

        return PaymentResponse.model_validate(payment)

    def process_webhook(
        self,
        provider: str | PaymentProvider,
        payload_bytes: bytes,
        headers: Dict[str, str],
    ) -> Dict[str, Any]:
        strategy = PaymentStrategyFactory.get_strategy(provider)
        result = strategy.handle_webhook(payload_bytes, headers)

        status_str = result.get("status")
        transaction_id = result.get("transaction_id")
        payment_id_str = result.get("payment_id")
        order_id_str = result.get("order_id")

        payment = None
        if payment_id_str:
            payment = self.payment_repo.get_by_id(payment_id_str)
        elif transaction_id:
            payment = self.payment_repo.get_by_transaction_id(transaction_id)

        if not payment and order_id_str:
            order = self.order_repo.get_by_id(order_id_str)
            if order and order.payments:
                payment = order.payments[-1]

        if not payment:
            logger.warning(f"Webhook received for unknown transaction {transaction_id} / payment {payment_id_str}")
            return {"status": "ignored", "message": "Payment record not found"}

        if status_str == "successful":
            self._fulfill_successful_payment(
                payment.id,
                transaction_id=transaction_id or payment.transaction_id or "tx_confirmed",
                raw_response=json.dumps(result.get("raw_payload", {})),
            )
            return {"status": "fulfilled", "payment_id": str(payment.id)}
        elif status_str == "failed":
            self.payment_repo.update_status(
                payment,
                status=PaymentStatus.FAILED,
                transaction_id=transaction_id,
                gateway_response=json.dumps(result.get("raw_payload", {})),
            )
            return {"status": "failed", "payment_id": str(payment.id)}

        return {"status": "pending", "payment_id": str(payment.id)}

    def execute_and_verify(self, payment_id: str | uuid.UUID, verification_payload: Dict[str, Any]) -> PaymentResponse:
        payment = self.payment_repo.get_by_id(payment_id)
        if not payment:
            raise NotFoundError("Payment not found")

        if payment.status == PaymentStatus.SUCCESSFUL:
            return PaymentResponse.model_validate(payment)

        strategy = PaymentStrategyFactory.get_strategy(payment.provider)
        result = strategy.verify_payment(payment, verification_payload)

        if result.get("status") == "successful":
            tx_id = result.get("transaction_id") or payment.transaction_id or "tx_verified"
            self._fulfill_successful_payment(
                payment.id,
                transaction_id=tx_id,
                raw_response=json.dumps(result),
            )
            # Re-fetch updated
            updated_payment = self.payment_repo.get_by_id(payment.id)
            return PaymentResponse.model_validate(updated_payment)
        else:
            self.payment_repo.update_status(
                payment,
                status=PaymentStatus.FAILED,
                gateway_response=json.dumps(result),
            )
            updated_payment = self.payment_repo.get_by_id(payment.id)
            return PaymentResponse.model_validate(updated_payment)

    def _fulfill_successful_payment(
        self,
        payment_id: uuid.UUID,
        transaction_id: str,
        raw_response: str,
    ) -> None:
        """
        Executes stock decrement and transitions order status to PAID inside
        a single atomic database transaction.
        """
        with self.session_manager.session() as session:
            payment = session.get(Payment, payment_id)
            if not payment:
                return

            if payment.status == PaymentStatus.SUCCESSFUL:
                logger.info(f"Payment {payment_id} is already fulfilled. Skipping idempotently.")
                return

            order = session.execute(
                select(Order).options(selectinload(Order.items)).where(Order.id == payment.order_id)
            ).scalar_one_or_none()
            if not order:
                raise NotFoundError("Order for payment not found")

            # Check and atomically decrement stock for each order item
            for item in order.items:
                stock_decremented = self.product_repo.decrement_stock_atomic(
                    product_id=item.product_id,
                    quantity=item.quantity,
                    session=session,
                )
                if not stock_decremented:
                    logger.error(
                        f"Stock decrement failed for product {item.product_id} in order {order.id}. Stock insufficient."
                    )
                    payment.status = PaymentStatus.FAILED
                    payment.gateway_response = raw_response
                    order.status = OrderStatus.FAILED
                    session.add(payment)
                    session.add(order)
                    raise BadRequestError(
                        f"Stock allocation failed for product {item.product_id}. Available inventory exhausted."
                    )

            # Successfully update payment and order states
            payment.status = PaymentStatus.SUCCESSFUL
            payment.transaction_id = transaction_id
            payment.gateway_response = raw_response
            order.status = OrderStatus.PAID

            session.add(payment)
            session.add(order)
            logger.info(f"Payment {payment.id} verified and order {order.order_number} marked PAID. Inventory deducted.")
