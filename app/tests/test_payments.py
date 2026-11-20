from app.models.payment import PaymentProvider
from app.services.payment.factory import PaymentStrategyFactory
from app.services.payment.stripe import StripePaymentStrategy
from app.services.payment.bkash import BkashPaymentStrategy


def test_payment_strategy_factory():
    stripe_strategy = PaymentStrategyFactory.get_strategy(PaymentProvider.STRIPE)
    assert isinstance(stripe_strategy, StripePaymentStrategy)

    bkash_strategy = PaymentStrategyFactory.get_strategy(PaymentProvider.BKASH)
    assert isinstance(bkash_strategy, BkashPaymentStrategy)


def test_checkout_stripe(client, user_token, test_catalog):
    # 1. Create order
    product = test_catalog["product"]
    order_res = client.post(
        "/api/v1/orders/",
        json={
            "items": [{"product_id": str(product.id), "quantity": 1}],
            "shipping_address": "Payment St",
        },
        headers={"Authorization": f"Bearer {user_token}"},
    )
    order_id = order_res.json()["id"]

    # 2. Checkout via Stripe
    checkout_res = client.post(
        "/api/v1/payments/checkout",
        json={
            "order_id": order_id,
            "provider": "stripe",
            "currency": "USD",
        },
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert checkout_res.status_code == 201
    data = checkout_res.json()
    assert data["order_id"] == order_id
    assert data["provider"] == "stripe"
    assert data["status"] == "pending"
    assert "client_secret" in data or "checkout_url" in data


def test_checkout_bkash(client, user_token, test_catalog):
    # 1. Create order
    product = test_catalog["product"]
    order_res = client.post(
        "/api/v1/orders/",
        json={
            "items": [{"product_id": str(product.id), "quantity": 1}],
            "shipping_address": "Dhaka, Bangladesh",
        },
        headers={"Authorization": f"Bearer {user_token}"},
    )
    order_id = order_res.json()["id"]

    # 2. Checkout via bKash
    checkout_res = client.post(
        "/api/v1/payments/checkout",
        json={
            "order_id": order_id,
            "provider": "bkash",
            "currency": "BDT",
            "return_url": "https://myapp.com/callback",
        },
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert checkout_res.status_code == 201
    data = checkout_res.json()
    assert data["provider"] == "bkash"
    assert "checkout_url" in data or "transaction_id" in data
