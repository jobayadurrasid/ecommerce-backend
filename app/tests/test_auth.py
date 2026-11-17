def test_register_user(client):
    payload = {
        "first_name": "Jane",
        "last_name": "Doe",
        "email": "jane@example.com",
        "password": "SecretPassword123",
        "address": "456 Market St",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "jane@example.com"
    assert data["first_name"] == "Jane"
    assert data["role"] == "customer"
    assert data["is_active"] is True


def test_register_duplicate_email(client, test_user):
    payload = {
        "first_name": "Duplicate",
        "last_name": "User",
        "email": test_user.email,
        "password": "SomePassword123",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 409
    data = response.json()
    assert data["code"] == "CONFLICT"


def test_login_success(client, test_user):
    payload = {
        "email": test_user.email,
        "password": "Password123!",
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_password(client, test_user):
    payload = {
        "email": test_user.email,
        "password": "WrongPassword",
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401


def test_get_current_user_me(client, test_user, user_token):
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user.email
    assert data["first_name"] == test_user.first_name


def test_refresh_token(client, test_user):
    # First login to get refresh token
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": test_user.email, "password": "Password123!"},
    )
    refresh_token = login_resp.json()["refresh_token"]

    refresh_resp = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_resp.status_code == 200
    data = refresh_resp.json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_create_admin_by_admin(client, test_admin, admin_token):
    payload = {
        "first_name": "Co",
        "last_name": "Admin",
        "email": "coadmin@example.com",
        "password": "AdminPassword123!",
        "address": "Operations Center",
    }
    response = client.post(
        "/api/v1/auth/create-admin",
        json=payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "coadmin@example.com"
    assert data["role"] == "admin"


def test_create_admin_forbidden_for_customer(client, test_admin, user_token):
    payload = {
        "first_name": "Rogue",
        "last_name": "Admin",
        "email": "rogue@example.com",
        "password": "AdminPassword123!",
    }
    response = client.post(
        "/api/v1/auth/create-admin",
        json=payload,
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 403
    assert "Admin privileges required" in response.json()["message"]


def test_create_admin_bootstrap_when_no_admins_exist(client):
    # Fresh database without any admin
    payload = {
        "first_name": "First",
        "last_name": "Admin",
        "email": "firstadmin@example.com",
        "password": "AdminPassword123!",
    }
    response = client.post(
        "/api/v1/auth/create-admin",
        json=payload,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "firstadmin@example.com"
    assert data["role"] == "admin"
