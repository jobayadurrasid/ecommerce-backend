import json
from app.database.session import SessionManager
from app.models.product import Product


def test_stripe_webhook_fulfill_and_stock_decrement(client, user_token, test_catalog):
    product = test_catalog["product"]
    initial_stock = product.stock  # 10

    # 1. Place order for 2 items
    order_res = client.post(
        "/api/v1/orders/",
        json={
            "items": [{"product_id": str(product.id), "quantity": 2}],
            "shipping_address": "Webhook Blvd",
        },
        headers={"Authorization": f"Bearer {user_token}"},
    )
    order_id = order_res.json()["id"]

    # 2. Initiate Stripe checkout
    checkout_res = client.post(
        "/api/v1/payments/checkout",
        json={
            "order_id": order_id,
            "provider": "stripe",
            "currency": "USD",
        },
        headers={"Authorization": f"Bearer {user_token}"},
    )
    payment_id = checkout_res.json()["payment_id"]

    # 3. Simulate Stripe webhook payload
    webhook_payload = {
        "id": "evt_test_webhook_123",
        "type": "payment_intent.succeeded",
        "data": {
            "object": {
                "id": "pi_test_tx_999",
                "amount": 252000,
                "metadata": {
                    "payment_id": payment_id,
                    "order_id": order_id,
                },
            }
        },
    }

    response = client.post(
        "/api/v1/payments/webhook/stripe",
        content=json.dumps(webhook_payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "fulfilled"

    # 4. Verify order is now PAID
    order_check = client.get(
        f"/api/v1/orders/{order_id}",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert order_check.json()["status"] == "paid"

    # 5. Verify stock was decremented from 10 to 8 in database
    manager = SessionManager()
    with manager.session() as db:
        updated_product = db.get(Product, product.id)
        assert updated_product.stock == initial_stock - 2

    # 6. Test Idempotency: Trigger same webhook again
    dup_res = client.post(
        "/api/v1/payments/webhook/stripe",
        content=json.dumps(webhook_payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    assert dup_res.status_code == 200

    # Verify stock remained at 8 (did not decrement a second time)
    with manager.session() as db:
        updated_product = db.get(Product, product.id)
        assert updated_product.stock == initial_stock - 2


def test_bkash_webhook_fulfillment(client, user_token, test_catalog):
    product = test_catalog["product"]

    # 1. Place order
    order_res = client.post(
        "/api/v1/orders/",
        json={
            "items": [{"product_id": str(product.id), "quantity": 1}],
            "shipping_address": "Gulshan, Dhaka",
        },
        headers={"Authorization": f"Bearer {user_token}"},
    )
    order_id = order_res.json()["id"]

    # 2. Checkout with bKash
    checkout_res = client.post(
        "/api/v1/payments/checkout",
        json={
            "order_id": order_id,
            "provider": "bkash",
            "currency": "BDT",
        },
        headers={"Authorization": f"Bearer {user_token}"},
    )
    payment_id = checkout_res.json()["payment_id"]

    # 3. Simulate bKash callback webhook
    webhook_payload = {
        "payment_id": payment_id,
        "order_id": order_id,
        "paymentID": f"BKASH_{payment_id}",
        "trxID": "TRX_BKASH_SUCCESS_789",
        "transactionStatus": "Completed",
        "amount": "1260.00",
    }

    response = client.post(
        "/api/v1/payments/webhook/bkash",
        content=json.dumps(webhook_payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "fulfilled"

    # 4. Verify order is PAID
    order_check = client.get(
        f"/api/v1/orders/{order_id}",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert order_check.json()["status"] == "paid"
