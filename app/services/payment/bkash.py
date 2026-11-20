import json
from typing import Optional, Dict, Any
import httpx

from app.core.config import settings
from app.core.exceptions import BadRequestError
from app.core.logger import logger
from app.models.payment import Payment
from app.models.order import Order
from app.services.payment.base import PaymentStrategy


class BkashPaymentStrategy(PaymentStrategy):
    def __init__(self):
        self.base_url = settings.BKASH_BASE_URL or "https://tokenized.sandbox.bka.sh/v2.0-beta"
        self.app_key = settings.BKASH_APP_KEY
        self.app_secret = settings.BKASH_APP_SECRET
        self.username = settings.BKASH_USERNAME
        self.password = settings.BKASH_PASSWORD

    def _get_token(self) -> str:
        if not (self.app_key and self.app_secret and self.username and self.password):
            return "mock_bkash_id_token"

        url = f"{self.base_url}/tokenized/checkout/token/grant"
        headers = {
            "Content-Type": "application/json",
            "username": self.username,
            "password": self.password,
        }
        data = {
            "app_key": self.app_key,
            "app_secret": self.app_secret,
        }

        try:
            with httpx.Client(timeout=10) as client:
                resp = client.post(url, headers=headers, json=data)
                resp_json = resp.json()
                return resp_json.get("id_token", "")
        except Exception as e:
            logger.error(f"bKash token grant error: {e}")
            raise BadRequestError(f"bKash auth failed: {str(e)}")

    def create_checkout_session(
        self,
        payment: Payment,
        order: Order,
        return_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        # Local/Test fallback when credentials not provided
        if not (self.app_key and self.app_secret):
            mock_payment_id = f"BKASH_MOCK_{payment.id.hex[:12]}"
            return {
                "checkout_url": f"https://sandbox.payment.bkash.com/redirect/{mock_payment_id}",
                "transaction_id": mock_payment_id,
                "client_secret": None,
                "metadata": {"payment_id_bkash": mock_payment_id},
            }

        token = self._get_token()
        url = f"{self.base_url}/tokenized/checkout/create"
        headers = {
            "Content-Type": "application/json",
            "Authorization": token,
            "X-APP-Key": self.app_key,
        }
        data = {
            "mode": "0011",
            "payerReference": str(order.user_id),
            "callbackURL": return_url or "https://example.com/payment/callback",
            "amount": str(payment.amount),
            "currency": "BDT",
            "intent": "sale",
            "merchantInvoiceNumber": order.order_number,
        }

        try:
            with httpx.Client(timeout=10) as client:
                resp = client.post(url, headers=headers, json=data)
                resp_json = resp.json()
                bkash_payment_id = resp_json.get("paymentID")
                bkash_url = resp_json.get("bkashURL")
                return {
                    "checkout_url": bkash_url,
                    "transaction_id": bkash_payment_id,
                    "client_secret": None,
                    "metadata": resp_json,
                }
        except Exception as e:
            logger.error(f"bKash checkout create failed: {e}")
            raise BadRequestError(f"bKash checkout error: {str(e)}")

    def verify_payment(self, payment: Payment, payload: Dict[str, Any]) -> Dict[str, Any]:
        bkash_payment_id = payload.get("payment_id_bkash") or payment.transaction_id
        if not bkash_payment_id:
            raise BadRequestError("Missing bKash payment ID for verification.")

        if not (self.app_key and self.app_secret):
            return {
                "status": "successful",
                "transaction_id": bkash_payment_id,
                "trx_id": f"TRX_{bkash_payment_id}",
            }

        token = self._get_token()
        url = f"{self.base_url}/tokenized/checkout/execute"
        headers = {
            "Content-Type": "application/json",
            "Authorization": token,
            "X-APP-Key": self.app_key,
        }
        data = {"paymentID": bkash_payment_id}

        try:
            with httpx.Client(timeout=10) as client:
                resp = client.post(url, headers=headers, json=data)
                resp_json = resp.json()
                status_code = resp_json.get("statusCode")
                status = "successful" if status_code == "0000" else "failed"
                return {
                    "status": status,
                    "transaction_id": resp_json.get("trxID") or bkash_payment_id,
                    "raw_response": resp_json,
                }
        except Exception as e:
            logger.error(f"bKash execute error: {e}")
            raise BadRequestError(f"bKash verification error: {str(e)}")

    def handle_webhook(self, payload: bytes, headers: Dict[str, str]) -> Dict[str, Any]:
        try:
            event = json.loads(payload.decode("utf-8"))
        except Exception:
            raise BadRequestError("Malformed JSON webhook payload.")

        # Extract standard bKash IPN / callback fields
        status_raw = event.get("transactionStatus") or event.get("status")
        status = "successful" if status_raw in ["Completed", "0000", "SUCCESS", "successful"] else "failed"

        return {
            "status": status,
            "transaction_id": event.get("trxID") or event.get("paymentID"),
            "payment_id": event.get("payment_id"),
            "order_id": event.get("order_id"),
            "raw_payload": event,
        }
