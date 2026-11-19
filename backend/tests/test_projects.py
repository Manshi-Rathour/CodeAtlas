def create_test_user(client, email):
    response = client.post(
        "/api/auth/signup",
        json={
            "full_name": "Project Test User",
            "email": email,
            "password": "TestPassword123"
        }
    )

    return response.json()["access_token"]


def test_create_project_success(client):
    token = create_test_user(client, "owner@example.com")

    response = client.post(
        "/api/projects/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Test Project",
            "description": "Testing project creation",
            "source_type": "manual"
        }
    )

    assert response.status_code == 201
    assert response.json()["name"] == "Test Project"


def test_get_user_projects(client):
    token = create_test_user(client, "list@example.com")

    client.post(
        "/api/projects/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "First Project",
            "source_type": "manual"
        }
    )

    response = client.get(
        "/api/projects/",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "First Project"


def test_get_project_by_id(client):
    token = create_test_user(client, "get@example.com")

    create_response = client.post(
        "/api/projects/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Project Details",
            "source_type": "manual"
        }
    )

    project_id = create_response.json()["id"]

    response = client.get(
        f"/api/projects/{project_id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert response.json()["id"] == project_id


def test_update_project(client):
    token = create_test_user(client, "update@example.com")

    create_response = client.post(
        "/api/projects/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Old Project Name",
            "source_type": "manual"
        }
    )

    project_id = create_response.json()["id"]

    response = client.patch(
        f"/api/projects/{project_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Updated Project Name"}
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Updated Project Name"


def test_delete_project(client):
    token = create_test_user(client, "delete@example.com")

    create_response = client.post(
        "/api/projects/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Project To Delete",
            "source_type": "manual"
        }
    )

    project_id = create_response.json()["id"]

    delete_response = client.delete(
        f"/api/projects/{project_id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert delete_response.status_code in (200, 204)

    get_response = client.get(
        f"/api/projects/{project_id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert get_response.status_code == 404


def test_user_cannot_access_another_users_project(client):
    owner_token = create_test_user(client, "owner2@example.com")
    other_token = create_test_user(client, "other@example.com")

    create_response = client.post(
        "/api/projects/",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={
            "name": "Private Project",
            "source_type": "manual"
        }
    )

    project_id = create_response.json()["id"]

    response = client.get(
        f"/api/projects/{project_id}",
        headers={"Authorization": f"Bearer {other_token}"}
    )

    assert response.status_code == 404


def test_create_project_without_token(client):
    response = client.post(
        "/api/projects/",
        json={
            "name": "Unauthorized Project",
            "source_type": "manual"
        }
    )

    assert response.status_code == 401


def test_delete_project_removes_imported_storage(
    client,
    db_session,
    tmp_path,
    monkeypatch,
):
    from app.core.config import settings
    from app.models.project import Project
    from app.models.user import User

    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))

    token = create_test_user(client, "delete-storage@example.com")

    user = (
        db_session.query(User)
        .filter(User.email == "delete-storage@example.com")
        .one()
    )

    storage_folder = tmp_path / str(user.id) / "storageid"
    source_folder = storage_folder / "source" / "project"
    source_folder.mkdir(parents=True)
    (source_folder / "app.py").write_text("print('hello')", encoding="utf-8")

    response = client.post(
        "/api/projects/",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Delete Storage Project", "source_type": "zip"},
    )

    project_id = response.json()["id"]

    project = (
        db_session.query(Project)
        .filter(Project.id == project_id)
        .one()
    )
    project.root_path = str(source_folder)
    db_session.commit()

    delete_response = client.delete(
        f"/api/projects/{project_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert delete_response.status_code == 200
    assert not storage_folder.exists()
