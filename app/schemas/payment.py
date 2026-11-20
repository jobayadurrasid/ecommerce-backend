from uuid import UUID
from decimal import Decimal
from typing import Optional, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from app.models.payment import PaymentProvider, PaymentStatus


class CheckoutRequest(BaseModel):
    order_id: UUID
    provider: PaymentProvider
    currency: str = Field(default="USD", max_length=3)
    return_url: Optional[str] = None


class CheckoutResponse(BaseModel):
    payment_id: UUID
    order_id: UUID
    provider: PaymentProvider
    amount: Decimal
    currency: str
    status: PaymentStatus
    checkout_url: Optional[str] = None
    client_secret: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    order_id: UUID
    provider: PaymentProvider
    transaction_id: Optional[str] = None
    status: PaymentStatus
    amount: Decimal
    currency: str
    created_at: datetime


class StripeWebhookPayload(BaseModel):
    pass


class BkashExecuteRequest(BaseModel):
    payment_id: UUID
    payment_id_bkash: str
