def test_create_order_success(client, user_token, test_catalog):
    product = test_catalog["product"]
    payload = {
        "items": [
            {
                "product_id": str(product.id),
                "quantity": 2,
            }
        ],
        "shipping_address": "789 Main Blvd, Silicon Valley",
    }
    response = client.post(
        "/api/v1/orders/",
        json=payload,
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "pending"
    # Price was 1200.00 * 2 = 2400.00 subtotal
    assert float(data["subtotal"]) == 2400.00
    # Tax: 2400 * 0.05 = 120.00
    assert float(data["tax"]) == 120.00
    assert float(data["total_amount"]) == 2520.00
    assert len(data["items"]) == 1
    assert data["items"][0]["quantity"] == 2


def test_create_order_exceeds_stock_fails(client, user_token, test_catalog):
    product = test_catalog["product"]
    payload = {
        "items": [
            {
                "product_id": str(product.id),
                "quantity": 999,  # available is 10
            }
        ],
        "shipping_address": "Some Street",
    }
    response = client.post(
        "/api/v1/orders/",
        json=payload,
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 400
    assert "Insufficient stock" in response.json()["message"]


def test_list_and_get_order(client, user_token, test_catalog):
    product = test_catalog["product"]
    order_res = client.post(
        "/api/v1/orders/",
        json={
            "items": [{"product_id": str(product.id), "quantity": 1}],
            "shipping_address": "Apt 4B",
        },
        headers={"Authorization": f"Bearer {user_token}"},
    )
    order_id = order_res.json()["id"]

    # Get single order
    get_res = client.get(
        f"/api/v1/orders/{order_id}",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert get_res.status_code == 200
    assert get_res.json()["id"] == order_id

    # List orders
    list_res = client.get(
        "/api/v1/orders/",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert list_res.status_code == 200
    assert list_res.json()["total"] >= 1


def test_cancel_order(client, user_token, test_catalog):
    product = test_catalog["product"]
    order_res = client.post(
        "/api/v1/orders/",
        json={
            "items": [{"product_id": str(product.id), "quantity": 1}],
            "shipping_address": "Apt 4B",
        },
        headers={"Authorization": f"Bearer {user_token}"},
    )
    order_id = order_res.json()["id"]

    cancel_res = client.post(
        f"/api/v1/orders/{order_id}/cancel",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "cancelled"
