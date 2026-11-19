from pathlib import Path

from app.models.chat import Chat
from app.models.documentation import Documentation
from app.models.project import Project


def _create_user(client, email):
    response = client.post(
        "/api/auth/signup",
        json={
            "full_name": "API Test User",
            "email": email,
            "password": "TestPassword123",
        },
    )

    assert response.status_code == 201, response.text

    return response.json()["access_token"]


def _create_project(db_session, token, client, name):
    response = client.post(
        "/api/projects/",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": name, "source_type": "manual"},
    )

    assert response.status_code == 201, response.text

    return response.json()["id"]


def _write_project_file(
    db_session,
    project_id,
    tmp_path,
    relative_path,
    content,
    language="Python",
):
    from app.models.project_file import ProjectFile

    source_path = tmp_path / relative_path
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text(content, encoding="utf-8")

    project = db_session.query(Project).filter(
        Project.id == project_id
    ).first()
    project.root_path = str(tmp_path)

    record = ProjectFile(
        project_id=project_id,
        filename=Path(relative_path).name,
        relative_path=relative_path,
        extension=Path(relative_path).suffix,
        language=language,
        size_bytes=source_path.stat().st_size,
    )

    db_session.add(record)
    db_session.commit()

    return record


def _route_headers(token):
    return {"Authorization": f"Bearer {token}"}


def test_detects_flask_routes(client, db_session, tmp_path):
    token = _create_user(client, "apis-flask@example.com")
    project_id = _create_project(
        db_session, token, client, "Flask API Project"
    )

    _write_project_file(
        db_session,
        project_id,
        tmp_path,
        "app.py",
        (
            "from flask import Flask\n"
            "app = Flask(__name__)\n\n"
            "@app.route('/health')\n"
            "def health():\n"
            "    return 'ok'\n\n"
            "@app.route('/items', methods=['GET', 'POST'])\n"
            "def items():\n"
            "    return 'items'\n\n"
            "@app.get('/profile')\n"
            "def profile():\n"
            "    return 'profile'\n"
        ),
    )

    _write_project_file(
        db_session,
        project_id,
        tmp_path,
        "templates/index.html",
        "<html><body>Hello</body></html>",
        language="HTML",
    )

    _write_project_file(
        db_session,
        project_id,
        tmp_path,
        "requirements.txt",
        "Flask==3.0.0\n",
        language="Other",
    )

    response = client.get(
        f"/api/projects/{project_id}/apis",
        headers=_route_headers(token),
    )

    assert response.status_code == 200, response.text

    payload = response.json()

    assert payload["total"] == 4
    assert payload["frameworks"] == ["Flask"]

    found = {
        (endpoint["method"], endpoint["path"])
        for endpoint in payload["endpoints"]
    }

    assert found == {
        ("GET", "/health"),
        ("GET", "/items"),
        ("POST", "/items"),
        ("GET", "/profile"),
    }

    assert all(
        endpoint["file"] == "app.py"
        and endpoint["line"] > 0
        for endpoint in payload["endpoints"]
    )


def test_detects_express_routes(client, db_session, tmp_path):
    token = _create_user(client, "apis-express@example.com")
    project_id = _create_project(
        db_session, token, client, "Express API Project"
    )

    _write_project_file(
        db_session,
        project_id,
        tmp_path,
        "src/server.js",
        (
            "const express = require('express');\n"
            "const app = express();\n"
            "const router = express.Router();\n\n"
            "app.get('/api/users', (req, res) => res.json([]));\n"
            "router.post('/api/users', (req, res) => res.json({}));\n"
            "router.delete('/api/users/:id', (req, res) => res.json({}));\n"
        ),
        language="JavaScript",
    )

    _write_project_file(
        db_session,
        project_id,
        tmp_path,
        "package.json",
        '{"dependencies": {"express": "^4.19.0"}}',
        language="JSON",
    )

    response = client.get(
        f"/api/projects/{project_id}/apis",
        headers=_route_headers(token),
    )

    assert response.status_code == 200, response.text

    payload = response.json()

    assert payload["total"] == 3
    assert payload["frameworks"] == ["Express.js"]

    assert {
        (endpoint["method"], endpoint["path"])
        for endpoint in payload["endpoints"]
    } == {
        ("GET", "/api/users"),
        ("POST", "/api/users"),
        ("DELETE", "/api/users/:id"),
    }


def test_ignores_routes_defined_inside_test_fixtures(
    client,
    db_session,
    tmp_path,
):
    token = _create_user(client, "apis-fixtures@example.com")
    project_id = _create_project(
        db_session, token, client, "Fixture API Project"
    )

    _write_project_file(
        db_session,
        project_id,
        tmp_path,
        "fixtures/server.js",
        "app.get('/fixture-only', handler);\n",
        language="JavaScript",
    )

    response = client.get(
        f"/api/projects/{project_id}/apis",
        headers=_route_headers(token),
    )

    assert response.status_code == 200, response.text
    assert response.json()["endpoints"] == []


def test_api_detection_rejects_another_users_project(
    client,
    db_session,
    tmp_path,
):
    owner_token = _create_user(client, "apis-owner@example.com")
    project_id = _create_project(
        db_session, owner_token, client, "Private API Project"
    )

    _write_project_file(
        db_session,
        project_id,
        tmp_path,
        "app.py",
        "@app.route('/private')\ndef private():\n    return 'x'\n",
    )

    other_token = _create_user(client, "apis-other@example.com")

    for path in ("apis", "metrics"):
        response = client.get(
            f"/api/projects/{project_id}/{path}",
            headers=_route_headers(other_token),
        )

        assert response.status_code == 404


def test_builds_project_metrics(
    client,
    db_session,
    tmp_path,
    register_user,
    project_factory,
    file_factory,
    symbol_factory,
    dependency_factory,
):
    user, headers = register_user("metrics-project@example.com")
    project = project_factory(user.id, "Metrics Project")

    main = file_factory(project.id, "app.py")
    helper = file_factory(project.id, "helper.py")

    symbol_factory(main.id, name="main", symbol_type="function")
    symbol_factory(main.id, name="Helper", symbol_type="class")
    symbol_factory(helper.id, name="format", symbol_type="function")
    symbol_factory(helper.id, name="use", symbol_type="method")

    dependency_factory(
        project_id=project.id,
        file_id=main.id,
        dependency_name="helper",
        resolved_file_id=helper.id,
    )
    dependency_factory(
        project_id=project.id,
        file_id=main.id,
        dependency_name="requests",
        resolved_file_id=None,
    )

    db_session.add(
        Documentation(project_id=project.id, content="# Docs")
    )
    db_session.add(
        Chat(
            conversation_id="metrics-conversation",
            user_id=user.id,
            project_id=project.id,
            role="user",
            content="How does this work?",
        )
    )
    db_session.commit()

    response = client.get(
        f"/api/projects/{project.id}/metrics",
        headers=headers,
    )

    assert response.status_code == 200, response.text

    payload = response.json()

    assert payload["project_id"] == project.id
    assert payload["project_name"] == "Metrics Project"
    assert payload["total_files"] == 2
    assert payload["symbols"] == {
        "total": 4,
        "functions": 2,
        "methods": 1,
        "classes": 1,
        "other": 0,
        "files_with_symbols": 2,
    }
    assert payload["dependencies"] == {
        "total": 2,
        "resolved": 1,
        "external": 1,
    }
    assert payload["conversations"] == 1
    assert payload["documentation"]["exists"] is True
    assert payload["languages"][0]["files"] == 2
    assert payload["api_endpoints"] == 0
