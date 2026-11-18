from pathlib import Path

import pytest

from app.api.routes import architecture as architecture_route


@pytest.fixture
def fake_architecture_ai(monkeypatch):
    captured = {}

    async def fake_explanation(architecture):
        captured["architecture"] = architecture
        return "# Overall Architecture\nGrounded explanation."

    monkeypatch.setattr(
        architecture_route,
        "generate_architecture_explanation",
        fake_explanation,
    )

    return captured


def _create_architecture_project(
    register_user,
    project_factory,
    file_factory,
    symbol_factory,
    dependency_factory,
    email,
):
    user, headers = register_user(email)
    project = project_factory(user.id, "Architecture Project")

    main = file_factory(project.id, "backend/app/main.py")
    auth = file_factory(project.id, "backend/app/services/auth.py")
    readme = file_factory(project.id, "README.md", language="Markdown")

    symbol_factory(
        main.id,
        name="create_app",
        symbol_type="function",
        start_line=1,
        end_line=10,
    )

    symbol_factory(
        auth.id,
        name="login",
        symbol_type="function",
        start_line=1,
        end_line=5,
    )

    dependency_factory(
        project_id=project.id,
        file_id=main.id,
        dependency_name="auth",
        line_number=3,
        resolved_file_id=auth.id,
    )

    dependency_factory(
        project_id=project.id,
        file_id=main.id,
        dependency_name="fastapi",
        line_number=1,
        resolved_file_id=None,
    )

    return user, headers, project, {
        "main": main,
        "auth": auth,
        "readme": readme,
    }


def test_architecture_reports_database_facts(
    client,
    register_user,
    project_factory,
    file_factory,
    symbol_factory,
    dependency_factory,
):
    user, headers, project, _ = _create_architecture_project(
        register_user,
        project_factory,
        file_factory,
        symbol_factory,
        dependency_factory,
        "architecture-facts@example.com",
    )

    response = client.get(
        f"/api/projects/{project.id}/architecture?include_ai=false",
        headers=headers,
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["project_id"] == project.id
    assert data["project_name"] == "Architecture Project"
    assert data["total_files"] == 3
    assert data["total_symbols"] == 2
    assert data["total_dependencies"] == 2
    assert data["total_internal_dependencies"] == 1
    assert data["ai_explanation"] is None

    languages = {
        item["language"]: item["file_count"]
        for item in data["languages"]
    }

    assert languages["Python"] == 2
    # Markdown is not a programming language.
    assert "Markdown" not in languages

    modules = {module["name"]: module for module in data["modules"]}

    assert "backend/app" in modules
    assert "backend/app/services" in modules
    assert "root" in modules

    assert modules["backend/app"]["file_count"] == 1
    assert modules["backend/app/services"]["file_count"] == 1
    assert modules["root"]["file_count"] == 1

    assert [
        symbol["name"]
        for symbol in modules["backend/app"]["symbols"]
    ] == ["create_app"]

    assert [
        symbol["name"]
        for symbol in modules["backend/app/services"]["symbols"]
    ] == ["login"]

    relationship = data["file_relationships"][0]

    assert relationship["source"] == "backend/app/main.py"
    assert relationship["target"] == "backend/app/services/auth.py"
    assert relationship["dependency"] == "auth"

    module_relationship = data["module_relationships"][0]

    assert module_relationship["source"] == "backend/app"
    assert module_relationship["target"] == "backend/app/services"
    assert module_relationship["dependency_count"] == 1

    assert "TOTAL FILES: 3" in data["architecture_summary"]
    assert "Python: 2 file(s)" in data["architecture_summary"]
    assert (
        "backend/app/main.py -> backend/app/services/auth.py"
        in data["architecture_summary"]
    )


def test_architecture_handles_project_without_dependencies(
    client,
    register_user,
    project_factory,
    file_factory,
    symbol_factory,
):
    user, headers = register_user("architecture-nodeps@example.com")
    project = project_factory(user.id, "No Dependency Project")

    source = file_factory(project.id, "main.go", language="Go")
    symbol_factory(source.id, name="main", symbol_type="function")

    response = client.get(
        f"/api/projects/{project.id}/architecture?include_ai=false",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total_dependencies"] == 0
    assert data["total_internal_dependencies"] == 0
    assert data["file_relationships"] == []
    assert data["module_relationships"] == []
    assert "INTERNAL FILE RELATIONSHIPS" in data["architecture_summary"]


def test_architecture_handles_project_without_symbols(
    client,
    register_user,
    project_factory,
    file_factory,
):
    user, headers = register_user("architecture-nosymbols@example.com")
    project = project_factory(user.id, "No Symbols Project")
    file_factory(project.id, "styles.css", language="CSS")

    response = client.get(
        f"/api/projects/{project.id}/architecture?include_ai=false",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total_symbols"] == 0
    assert data["modules"][0]["symbols"] == []


def test_architecture_returns_ai_explanation_grounded_in_facts(
    client,
    register_user,
    project_factory,
    file_factory,
    symbol_factory,
    dependency_factory,
    fake_architecture_ai,
):
    user, headers, project, _ = _create_architecture_project(
        register_user,
        project_factory,
        file_factory,
        symbol_factory,
        dependency_factory,
        "architecture-ai@example.com",
    )

    response = client.get(
        f"/api/projects/{project.id}/architecture",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["ai_explanation"] == (
        "# Overall Architecture\nGrounded explanation."
    )

    # The AI receives only database-derived architecture facts.
    supplied = fake_architecture_ai["architecture"]

    assert supplied["total_files"] == 3
    assert supplied["total_internal_dependencies"] == 1


def test_architecture_rejects_other_users(
    client,
    register_user,
    project_factory,
    file_factory,
):
    owner, _ = register_user("architecture-owner@example.com")
    _, other_headers = register_user("architecture-intruder@example.com")

    project = project_factory(owner.id, "Private Architecture")
    file_factory(project.id, "main.py")

    response = client.get(
        f"/api/projects/{project.id}/architecture?include_ai=false",
        headers=other_headers,
    )

    assert response.status_code == 404


def test_architecture_rejects_project_without_files(
    client,
    register_user,
    project_factory,
):
    user, headers = register_user("architecture-empty@example.com")
    project = project_factory(user.id, "Empty Architecture")

    response = client.get(
        f"/api/projects/{project.id}/architecture?include_ai=false",
        headers=headers,
    )

    assert response.status_code == 400
    assert "No project files" in response.json()["detail"]


def test_architecture_requires_authentication(
    client,
    register_user,
    project_factory,
    file_factory,
):
    user, _ = register_user("architecture-auth@example.com")
    project = project_factory(user.id, "Auth Architecture")
    file_factory(project.id, "main.py")

    response = client.get(f"/api/projects/{project.id}/architecture")

    assert response.status_code == 401
