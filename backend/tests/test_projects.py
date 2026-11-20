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
    assert not (tmp_path / str(user.id)).exists()


def test_architecture_indexes_project_without_inventory(
    client,
    db_session,
    tmp_path,
    monkeypatch,
):
    from app.core.config import settings
    from app.models.project import Project
    from app.models.project_file import ProjectFile
    from app.models.user import User

    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))

    token = create_test_user(client, "legacy-architecture@example.com")

    user = (
        db_session.query(User)
        .filter(User.email == "legacy-architecture@example.com")
        .one()
    )

    source_folder = (
        tmp_path / str(user.id) / "legacy-storage" / "source"
    )
    source_folder.mkdir(parents=True)
    (source_folder / "app.py").write_text(
        "def hello():\n    return 'hi'\n",
        encoding="utf-8",
    )

    response = client.post(
        "/api/projects/",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Legacy Architecture", "source_type": "zip"},
    )

    project_id = response.json()["id"]

    project = (
        db_session.query(Project)
        .filter(Project.id == project_id)
        .one()
    )
    project.root_path = str(source_folder)
    db_session.commit()

    assert (
        db_session.query(ProjectFile)
        .filter(ProjectFile.project_id == project_id)
        .count()
        == 0
    )

    architecture_response = client.get(
        f"/api/projects/{project_id}/architecture?include_ai=false",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert architecture_response.status_code == 200, (
        architecture_response.text
    )
    assert architecture_response.json()["total_files"] >= 1

    assert (
        db_session.query(ProjectFile)
        .filter(ProjectFile.project_id == project_id)
        .count()
        >= 1
    )


def test_project_summary_reports_analysis_status(client, db_session):
    from app.models.code_chunk import CodeChunk
    from app.models.project_file import ProjectFile

    token = create_test_user(client, "summary-status@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    first_response = client.post(
        "/api/projects/",
        headers=headers,
        json={"name": "Analyzed Project", "source_type": "zip"},
    )
    second_response = client.post(
        "/api/projects/",
        headers=headers,
        json={"name": "Awaiting Project", "source_type": "zip"},
    )

    analyzed_project_id = first_response.json()["id"]
    awaiting_project_id = second_response.json()["id"]

    project_file = ProjectFile(
        project_id=analyzed_project_id,
        filename="app.py",
        relative_path="app.py",
        extension=".py",
        language="python",
        size_bytes=24,
    )
    db_session.add(project_file)
    db_session.commit()
    db_session.refresh(project_file)

    db_session.add(
        CodeChunk(
            file_id=project_file.id,
            chunk_type="function",
            name="hello",
            start_line=1,
            end_line=2,
            content="def hello():\n    return 'hi'",
        )
    )
    db_session.commit()

    response = client.get("/api/projects/summary", headers=headers)

    assert response.status_code == 200, response.text

    rows = {row["id"]: row for row in response.json()}

    assert rows[analyzed_project_id]["has_analysis"] is True
    assert rows[awaiting_project_id]["has_analysis"] is False
