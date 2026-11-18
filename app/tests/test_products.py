def test_create_category_admin(client, admin_token):
    payload = {
        "name": "Smartphones",
        "slug": "smartphones",
        "description": "Mobile phones and tablets",
    }
    response = client.post(
        "/api/v1/categories/",
        json=payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Smartphones"


def test_create_category_forbidden_customer(client, user_token):
    payload = {
        "name": "Unauthorized Category",
        "slug": "unauthorized-cat",
    }
    response = client.post(
        "/api/v1/categories/",
        json=payload,
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 403


def test_list_categories_tree(client, test_catalog):
    response = client.get("/api/v1/categories/")
    assert response.status_code == 200
    tree = response.json()
    assert len(tree) >= 1
    root = tree[0]
    assert root["slug"] == "electronics"
    assert len(root["children"]) >= 1


def test_create_product_admin(client, admin_token, test_catalog):
    category_id = str(test_catalog["laptops"].id)
    payload = {
        "category_id": category_id,
        "name": "Gaming Beast 17",
        "slug": "gaming-beast-17",
        "sku": "SKU-GB-17",
        "description": "High end gaming laptop",
        "price": 2500.00,
        "stock": 5,
        "is_active": True,
    }
    response = client.post(
        "/api/v1/products/",
        json=payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 201
    assert response.json()["sku"] == "SKU-GB-17"


def test_create_duplicate_sku_fails(client, admin_token, test_catalog):
    category_id = str(test_catalog["laptops"].id)
    payload = {
        "category_id": category_id,
        "name": "Another Laptop",
        "slug": "another-laptop",
        "sku": test_catalog["product"].sku,
        "price": 999.00,
        "stock": 3,
    }
    response = client.post(
        "/api/v1/products/",
        json=payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 409


def test_category_recommendations_dfs(client, test_catalog):
    root_id = str(test_catalog["electronics"].id)
    response = client.get(f"/api/v1/categories/{root_id}/recommendations")
    assert response.status_code == 200
    recommendations = response.json()
    assert len(recommendations) >= 1
    # Verify the product under the deep child category 'laptops' is recommended
    assert any(p["sku"] == "SKU-LAPTOP-001" for p in recommendations)
