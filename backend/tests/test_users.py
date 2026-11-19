from pathlib import Path

from app.core.config import settings
from app.models.project import Project
from app.models.user import User


def test_update_profile_full_name(client, register_user):
    user, headers = register_user(
        "profile-name@example.com",
        full_name="Old Name",
    )

    response = client.patch(
        "/api/users/me",
        headers=headers,
        json={"full_name": "  New Profile Name  "},
    )

    assert response.status_code == 200, response.text

    payload = response.json()

    assert payload["full_name"] == "New Profile Name"
    assert payload["email"] == "profile-name@example.com"
    assert payload["created_at"]

    me = client.get("/api/auth/me", headers=headers)

    assert me.status_code == 200
    assert me.json()["full_name"] == "New Profile Name"


def test_update_profile_rejects_blank_name(client, register_user):
    user, headers = register_user("profile-blank@example.com")

    response = client.patch(
        "/api/users/me",
        headers=headers,
        json={"full_name": "   "},
    )

    assert response.status_code == 422


def test_change_password_then_login_with_new_password(
    client,
    register_user,
):
    user, headers = register_user("profile-password@example.com")

    response = client.post(
        "/api/users/me/password",
        headers=headers,
        json={
            "current_password": "TestPassword123",
            "new_password": "NewPassword456",
        },
    )

    assert response.status_code == 200, response.text

    old_login = client.post(
        "/api/auth/login",
        json={
            "email": "profile-password@example.com",
            "password": "TestPassword123",
        },
    )

    assert old_login.status_code == 401

    new_login = client.post(
        "/api/auth/login",
        json={
            "email": "profile-password@example.com",
            "password": "NewPassword456",
        },
    )

    assert new_login.status_code == 200


def test_change_password_requires_current_password(
    client,
    register_user,
):
    user, headers = register_user("profile-wrongpass@example.com")

    response = client.post(
        "/api/users/me/password",
        headers=headers,
        json={
            "current_password": "WrongPassword123",
            "new_password": "NewPassword456",
        },
    )

    assert response.status_code == 400

    login = client.post(
        "/api/auth/login",
        json={
            "email": "profile-wrongpass@example.com",
            "password": "TestPassword123",
        },
    )

    assert login.status_code == 200


def test_change_password_rejects_same_password(
    client,
    register_user,
):
    user, headers = register_user("profile-samepass@example.com")

    response = client.post(
        "/api/users/me/password",
        headers=headers,
        json={
            "current_password": "TestPassword123",
            "new_password": "TestPassword123",
        },
    )

    assert response.status_code == 400


def test_delete_account_removes_user_projects_and_storage(
    client,
    register_user,
    db_session,
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))

    user, headers = register_user("profile-delete@example.com")

    project_response = client.post(
        "/api/projects/",
        headers=headers,
        json={"name": "Account Project", "source_type": "zip"},
    )

    assert project_response.status_code == 201, project_response.text

    storage_folder = tmp_path / str(user.id) / "storageid"
    source_folder = storage_folder / "source"
    source_folder.mkdir(parents=True)
    (source_folder / "app.py").write_text("print('hi')", encoding="utf-8")

    response = client.delete("/api/users/me", headers=headers)

    assert response.status_code == 200, response.text
    assert response.json()["message"] == "Account deleted successfully."

    # The session token no longer resolves to a user.
    me = client.get("/api/auth/me", headers=headers)
    assert me.status_code == 401

    assert (
        db_session.query(User)
        .filter(User.email == "profile-delete@example.com")
        .count()
        == 0
    )
    assert (
        db_session.query(Project)
        .filter(Project.owner_id == user.id)
        .count()
        == 0
    )
    assert not storage_folder.exists()


def test_profile_endpoints_require_authentication(client):
    response = client.patch(
        "/api/users/me",
        json={"full_name": "No Auth"},
    )

    assert response.status_code == 401

    response = client.post(
        "/api/users/me/password",
        json={
            "current_password": "TestPassword123",
            "new_password": "NewPassword456",
        },
    )

    assert response.status_code == 401

    response = client.delete("/api/users/me")

    assert response.status_code == 401
