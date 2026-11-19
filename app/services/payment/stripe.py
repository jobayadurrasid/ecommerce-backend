import json
from decimal import Decimal
from typing import Optional, Dict, Any
import stripe

from app.core.config import settings
from app.core.exceptions import BadRequestError
from app.core.logger import logger
from app.models.payment import Payment
from app.models.order import Order
from app.services.payment.base import PaymentStrategy


class StripePaymentStrategy(PaymentStrategy):
    def __init__(self):
        if settings.STRIPE_SECRET_KEY:
            stripe.api_key = settings.STRIPE_SECRET_KEY

    def create_checkout_session(
        self,
        payment: Payment,
        order: Order,
        return_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        amount_cents = int(payment.amount * 100)
        currency = payment.currency.lower()

        # If running in local/test mode without API keys, return mock session
        if not settings.STRIPE_SECRET_KEY:
            mock_intent_id = f"pi_mock_{payment.id.hex[:14]}"
            return {
                "client_secret": f"{mock_intent_id}_secret_mock",
                "checkout_url": f"https://checkout.stripe.com/pay/{mock_intent_id}",
                "transaction_id": mock_intent_id,
            }

        try:
            intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency=currency,
                metadata={
                    "payment_id": str(payment.id),
                    "order_id": str(order.id),
                    "idempotency_key": payment.idempotency_key,
                },
            )
            return {
                "client_secret": intent.client_secret,
                "transaction_id": intent.id,
                "checkout_url": None,
            }
        except Exception as e:
            logger.error(f"Stripe payment intent creation error: {e}")
            raise BadRequestError(f"Stripe error: {str(e)}")

    def verify_payment(self, payment: Payment, payload: Dict[str, Any]) -> Dict[str, Any]:
        transaction_id = payload.get("transaction_id") or payment.transaction_id
        if not transaction_id:
            raise BadRequestError("Missing transaction ID for verification.")

        if not settings.STRIPE_SECRET_KEY:
            return {"status": "successful", "transaction_id": transaction_id}

        try:
            intent = stripe.PaymentIntent.retrieve(transaction_id)
            status = "successful" if intent.status == "succeeded" else "pending"
            return {"status": status, "transaction_id": intent.id}
        except Exception as e:
            logger.error(f"Stripe retrieve error: {e}")
            raise BadRequestError(f"Stripe error: {str(e)}")

    def handle_webhook(self, payload: bytes, headers: Dict[str, str]) -> Dict[str, Any]:
        sig_header = headers.get("stripe-signature")

        if settings.STRIPE_WEBHOOK_SECRET and sig_header:
            try:
                event = stripe.Webhook.construct_event(
                    payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
                )
            except Exception as e:
                logger.error(f"Stripe webhook signature verification failed: {e}")
                raise BadRequestError(f"Webhook signature error: {str(e)}")
        else:
            try:
                event = json.loads(payload.decode("utf-8"))
            except Exception:
                raise BadRequestError("Malformed JSON webhook payload.")

        event_type = event.get("type")
        data_object = event.get("data", {}).get("object", {})

        status = "pending"
        if event_type == "payment_intent.succeeded":
            status = "successful"
        elif event_type in ["payment_intent.payment_failed", "payment_intent.canceled"]:
            status = "failed"

        metadata = data_object.get("metadata", {})
        return {
            "status": status,
            "transaction_id": data_object.get("id"),
            "payment_id": metadata.get("payment_id"),
            "order_id": metadata.get("order_id"),
            "raw_payload": event,
        }
