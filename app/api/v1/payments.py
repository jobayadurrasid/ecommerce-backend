import uuid
from typing import Dict, Any
from fastapi import APIRouter, Depends, Request, status
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.payment import PaymentProvider
from app.schemas.payment import CheckoutRequest, CheckoutResponse, PaymentResponse, BkashExecuteRequest
from app.services.payment_service import PaymentService

router = APIRouter(
    prefix="/payments",
    tags=["Payments"],
)


@router.post(
    "/checkout",
    response_model=CheckoutResponse,
    status_code=status.HTTP_201_CREATED,
)
def checkout(
    payload: CheckoutRequest,
    current_user: User = Depends(get_current_user),
):
    service = PaymentService()
    return service.initiate_checkout(current_user, payload)


@router.get(
    "/{payment_id}",
    response_model=PaymentResponse,
    status_code=status.HTTP_200_OK,
)
def get_payment(
    payment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
):
    service = PaymentService()
    return service.get_payment_by_id(payment_id, current_user)


@router.post(
    "/execute",
    response_model=PaymentResponse,
    status_code=status.HTTP_200_OK,
)
def execute_payment(
    payload: BkashExecuteRequest,
    current_user: User = Depends(get_current_user),
):
    service = PaymentService()
    return service.execute_and_verify(payload.payment_id, payload.model_dump())


@router.post(
    "/webhook/stripe",
    status_code=status.HTTP_200_OK,
)
async def stripe_webhook(request: Request):
    payload = await request.body()
    headers = dict(request.headers)
    service = PaymentService()
    return service.process_webhook(PaymentProvider.STRIPE, payload, headers)


@router.post(
    "/webhook/bkash",
    status_code=status.HTTP_200_OK,
)
async def bkash_webhook(request: Request):
    payload = await request.body()
    headers = dict(request.headers)
    service = PaymentService()
    return service.process_webhook(PaymentProvider.BKASH, payload, headers)
