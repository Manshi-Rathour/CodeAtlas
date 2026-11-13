from pathlib import Path

from app.models.project import Project
from app.models.project_file import ProjectFile


def create_test_user(client, email):
    response = client.post(
        "/api/auth/signup",
        json={
            "full_name": "File Test User",
            "email": email,
            "password": "TestPassword123",
        },
    )

    assert response.status_code == 201

    return response.json()["access_token"]


def create_test_project(client, token, name):
    response = client.post(
        "/api/projects/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": name,
            "source_type": "manual",
        },
    )

    assert response.status_code == 201

    return response.json()["id"]


def add_test_file(
    db_session,
    project_id,
    tmp_path,
    filename="main.py",
    content='print("Hello CodeAtlas")\n',
):
    project_directory = tmp_path / f"project-{project_id}"
    project_directory.mkdir(exist_ok=True)

    source_file = project_directory / filename
    source_file.parent.mkdir(parents=True, exist_ok=True)
    source_file.write_text(content, encoding="utf-8")

    project = db_session.query(Project).filter(
        Project.id == project_id
    ).first()

    project.root_path = str(project_directory)

    project_file = ProjectFile(
        project_id=project_id,
        filename=Path(filename).name,
        relative_path=filename,
        extension=Path(filename).suffix.lstrip("."),
        language="Python",
        size_bytes=source_file.stat().st_size,
    )

    db_session.add(project_file)
    db_session.commit()
    db_session.refresh(project_file)

    return project_file.id


def test_user_can_list_own_project_files(
    client,
    db_session,
    tmp_path,
):
    token = create_test_user(
        client,
        "fileowner@example.com",
    )

    project_id = create_test_project(
        client,
        token,
        "File Listing Project",
    )

    add_test_file(
        db_session,
        project_id,
        tmp_path,
    )

    response = client.get(
        f"/api/projects/{project_id}/files",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["files"][0]["filename"] == "main.py"


def test_user_cannot_list_another_users_files(
    client,
    db_session,
    tmp_path,
):
    owner_token = create_test_user(
        client,
        "fileowner2@example.com",
    )

    other_token = create_test_user(
        client,
        "fileother@example.com",
    )

    project_id = create_test_project(
        client,
        owner_token,
        "Private File Project",
    )

    add_test_file(
        db_session,
        project_id,
        tmp_path,
    )

    response = client.get(
        f"/api/projects/{project_id}/files",
        headers={"Authorization": f"Bearer {other_token}"},
    )

    assert response.status_code == 404


def test_user_can_read_own_project_file(
    client,
    db_session,
    tmp_path,
):
    token = create_test_user(
        client,
        "sourceowner@example.com",
    )

    project_id = create_test_project(
        client,
        token,
        "Source Code Project",
    )

    file_id = add_test_file(
        db_session,
        project_id,
        tmp_path,
    )

    response = client.get(
        f"/api/projects/{project_id}/files/{file_id}/content",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["filename"] == "main.py"
    assert response.json()["content"] == 'print("Hello CodeAtlas")\n'


def test_user_cannot_read_another_users_source_code(
    client,
    db_session,
    tmp_path,
):
    owner_token = create_test_user(
        client,
        "sourceowner2@example.com",
    )

    other_token = create_test_user(
        client,
        "sourceother@example.com",
    )

    project_id = create_test_project(
        client,
        owner_token,
        "Private Source Project",
    )

    file_id = add_test_file(
        db_session,
        project_id,
        tmp_path,
    )

    response = client.get(
        f"/api/projects/{project_id}/files/{file_id}/content",
        headers={"Authorization": f"Bearer {other_token}"},
    )

    assert response.status_code == 404


def test_user_cannot_access_file_from_another_project(
    client,
    db_session,
    tmp_path,
):
    token = create_test_user(
        client,
        "crossproject@example.com",
    )

    first_project_id = create_test_project(
        client,
        token,
        "First Project",
    )

    second_project_id = create_test_project(
        client,
        token,
        "Second Project",
    )

    second_file_id = add_test_file(
        db_session,
        second_project_id,
        tmp_path,
    )

    response = client.get(
        f"/api/projects/{first_project_id}/files/{second_file_id}/content",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
