from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from app.models.payment import Payment
from app.models.order import Order


class PaymentStrategy(ABC):
    @abstractmethod
    def create_checkout_session(
        self,
        payment: Payment,
        order: Order,
        return_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Initiates a payment session with the gateway provider.
        Returns provider-specific data (e.g. client_secret, checkout_url).
        """
        pass

    @abstractmethod
    def verify_payment(self, payment: Payment, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Actively verifies a payment status with the gateway provider.
        """
        pass

    @abstractmethod
    def handle_webhook(self, payload: bytes, headers: Dict[str, str]) -> Dict[str, Any]:
        """
        Verifies signature and extracts payment status and transaction IDs from incoming webhook.
        Returns dict containing:
          - 'status': 'successful' | 'failed' | 'pending'
          - 'transaction_id': str
          - 'payment_id': Optional[str]
          - 'order_id': Optional[str]
          - 'raw_payload': dict
        """
        pass
