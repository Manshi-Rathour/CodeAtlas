def test_user_signup_success(client):
    response = client.post(
        "/api/auth/signup",
        json={
            "full_name": "Test User",
            "email": "test@example.com",
            "password": "TestPassword123"
        }
    )

    assert response.status_code == 201

    data = response.json()

    assert data["user"]["full_name"] == "Test User"
    assert data["user"]["email"] == "test@example.com"
    assert "access_token" in data


def test_user_signup_duplicate_email(client):
    user_data = {
        "full_name": "Test User",
        "email": "duplicate@example.com",
        "password": "TestPassword123"
    }

    first_response = client.post(
        "/api/auth/signup",
        json=user_data
    )

    second_response = client.post(
        "/api/auth/signup",
        json=user_data
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409


def test_user_signup_invalid_password(client):
    response = client.post(
        "/api/auth/signup",
        json={
            "full_name": "Test User",
            "email": "weak@example.com",
            "password": "123"
        }
    )

    assert response.status_code == 422


def test_user_login_success(client):
    client.post(
        "/api/auth/signup",
        json={
            "full_name": "Login User",
            "email": "login@example.com",
            "password": "TestPassword123"
        }
    )

    response = client.post(
        "/api/auth/login",
        json={
            "email": "login@example.com",
            "password": "TestPassword123"
        }
    )

    assert response.status_code == 200
    assert "access_token" in response.json()


def test_user_login_wrong_password(client):
    client.post(
        "/api/auth/signup",
        json={
            "full_name": "Login User",
            "email": "wrongpass@example.com",
            "password": "TestPassword123"
        }
    )

    response = client.post(
        "/api/auth/login",
        json={
            "email": "wrongpass@example.com",
            "password": "WrongPassword123"
        }
    )

    assert response.status_code == 401


def test_get_current_user_success(client):
    signup_response = client.post(
        "/api/auth/signup",
        json={
            "full_name": "Current User",
            "email": "current@example.com",
            "password": "TestPassword123"
        }
    )

    token = signup_response.json()["access_token"]

    response = client.get(
        "/api/auth/me",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 200
    assert response.json()["email"] == "current@example.com"


def test_get_current_user_without_token(client):
    response = client.get("/api/auth/me")

    assert response.status_code == 401
