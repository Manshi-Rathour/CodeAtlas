import pytest

from app.models.documentation import Documentation
from app.services.documentation import documentation_service


@pytest.fixture
def fake_documentation_ai(monkeypatch):
    captured = {"calls": 0}

    async def fake_generate(prompt, system_prompt=None):
        captured["calls"] += 1
        captured["prompt"] = prompt
        captured["system_prompt"] = system_prompt

        return f"# Project Overview\nGenerated documentation {captured['calls']}."

    monkeypatch.setattr(
        documentation_service.ollama_service,
        "generate_response",
        fake_generate,
    )

    return captured


def _create_documentable_project(
    register_user,
    project_factory,
    file_factory,
    symbol_factory,
    chunk_factory,
    dependency_factory,
    email,
):
    user, headers = register_user(email)
    project = project_factory(user.id, "Documentation Project")

    main = file_factory(project.id, "src/main.py")
    helpers = file_factory(project.id, "src/helpers.py")

    symbol_factory(
        main.id,
        name="main",
        source_code="def main():\n    return helper()\n",
    )
    chunk_factory(
        main.id,
        name="main",
        content="def main():\n    return helper()\n",
    )
    dependency_factory(
        project_id=project.id,
        file_id=main.id,
        dependency_name="helpers",
        resolved_file_id=helpers.id,
    )

    return user, headers, project


def test_documentation_generation_persists_record(
    client,
    register_user,
    project_factory,
    file_factory,
    symbol_factory,
    chunk_factory,
    dependency_factory,
    fake_documentation_ai,
    db_session,
):
    user, headers, project = _create_documentable_project(
        register_user,
        project_factory,
        file_factory,
        symbol_factory,
        chunk_factory,
        dependency_factory,
        "documentation-generate@example.com",
    )

    response = client.post(
        f"/api/projects/{project.id}/documentation",
        headers=headers,
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["project_id"] == project.id
    assert data["content"].startswith("# Project Overview")

    stored = (
        db_session.query(Documentation)
        .filter(Documentation.project_id == project.id)
        .all()
    )

    assert len(stored) == 1
    assert stored[0].content == data["content"]

    # Real project context is supplied to the model.
    prompt = fake_documentation_ai["prompt"]

    assert "src/main.py" in prompt
    assert "def main()" in prompt
    assert "helpers" in prompt
    assert "PROJECT CONTEXT" in prompt
    assert "untrusted" in fake_documentation_ai["system_prompt"].lower()


def test_documentation_can_be_retrieved_and_status_checked(
    client,
    register_user,
    project_factory,
    file_factory,
    symbol_factory,
    chunk_factory,
    dependency_factory,
    fake_documentation_ai,
):
    user, headers, project = _create_documentable_project(
        register_user,
        project_factory,
        file_factory,
        symbol_factory,
        chunk_factory,
        dependency_factory,
        "documentation-retrieve@example.com",
    )

    status_before = client.get(
        f"/api/projects/{project.id}/documentation/status",
        headers=headers,
    )

    assert status_before.status_code == 200
    assert status_before.json()["exists"] is False

    missing = client.get(
        f"/api/projects/{project.id}/documentation",
        headers=headers,
    )

    assert missing.status_code == 404

    generated = client.post(
        f"/api/projects/{project.id}/documentation",
        headers=headers,
    ).json()

    retrieved = client.get(
        f"/api/projects/{project.id}/documentation",
        headers=headers,
    )

    assert retrieved.status_code == 200
    assert retrieved.json()["content"] == generated["content"]

    status_after = client.get(
        f"/api/projects/{project.id}/documentation/status",
        headers=headers,
    )

    assert status_after.status_code == 200
    assert status_after.json()["exists"] is True


def test_documentation_regeneration_updates_same_record(
    client,
    register_user,
    project_factory,
    file_factory,
    symbol_factory,
    chunk_factory,
    dependency_factory,
    fake_documentation_ai,
    db_session,
):
    user, headers, project = _create_documentable_project(
        register_user,
        project_factory,
        file_factory,
        symbol_factory,
        chunk_factory,
        dependency_factory,
        "documentation-regenerate@example.com",
    )

    first = client.post(
        f"/api/projects/{project.id}/documentation",
        headers=headers,
    ).json()

    second = client.post(
        f"/api/projects/{project.id}/documentation",
        headers=headers,
    ).json()

    assert first["id"] == second["id"]
    assert first["content"] != second["content"]

    stored = (
        db_session.query(Documentation)
        .filter(Documentation.project_id == project.id)
        .all()
    )

    assert len(stored) == 1
    assert stored[0].content == second["content"]


def test_documentation_is_isolated_between_users(
    client,
    register_user,
    project_factory,
    file_factory,
    symbol_factory,
    chunk_factory,
    dependency_factory,
    fake_documentation_ai,
):
    owner, owner_headers, project = _create_documentable_project(
        register_user,
        project_factory,
        file_factory,
        symbol_factory,
        chunk_factory,
        dependency_factory,
        "documentation-owner@example.com",
    )

    _, other_headers = register_user("documentation-intruder@example.com")

    generated = client.post(
        f"/api/projects/{project.id}/documentation",
        headers=owner_headers,
    )

    assert generated.status_code == 200

    for method, path in (
        (client.get, f"/api/projects/{project.id}/documentation"),
        (client.get, f"/api/projects/{project.id}/documentation/status"),
        (client.post, f"/api/projects/{project.id}/documentation"),
    ):
        response = method(path, headers=other_headers)

        assert response.status_code == 404


def test_documentation_requires_project_files(
    client,
    register_user,
    project_factory,
):
    user, headers = register_user("documentation-empty@example.com")
    project = project_factory(user.id, "Empty Documentation")

    response = client.post(
        f"/api/projects/{project.id}/documentation",
        headers=headers,
    )

    assert response.status_code == 400
    assert "No project files" in response.json()["detail"]


def test_documentation_returns_503_when_ollama_fails(
    client,
    register_user,
    project_factory,
    file_factory,
    symbol_factory,
    chunk_factory,
    dependency_factory,
    monkeypatch,
    db_session,
):
    user, headers, project = _create_documentable_project(
        register_user,
        project_factory,
        file_factory,
        symbol_factory,
        chunk_factory,
        dependency_factory,
        "documentation-offline@example.com",
    )

    async def failing_generate(prompt, system_prompt=None):
        raise RuntimeError("Ollama request timed out. Please try again.")

    monkeypatch.setattr(
        documentation_service.ollama_service,
        "generate_response",
        failing_generate,
    )

    response = client.post(
        f"/api/projects/{project.id}/documentation",
        headers=headers,
    )

    assert response.status_code == 503

    assert db_session.query(Documentation).filter(
        Documentation.project_id == project.id
    ).count() == 0


def test_documentation_returns_503_for_empty_ai_response(
    client,
    register_user,
    project_factory,
    file_factory,
    symbol_factory,
    chunk_factory,
    dependency_factory,
    monkeypatch,
):
    user, headers, project = _create_documentable_project(
        register_user,
        project_factory,
        file_factory,
        symbol_factory,
        chunk_factory,
        dependency_factory,
        "documentation-emptyai@example.com",
    )

    async def empty_generate(prompt, system_prompt=None):
        return ""

    monkeypatch.setattr(
        documentation_service.ollama_service,
        "generate_response",
        empty_generate,
    )

    response = client.post(
        f"/api/projects/{project.id}/documentation",
        headers=headers,
    )

    assert response.status_code == 503


def test_documentation_keeps_setup_code_blocks_and_removes_links(
    client,
    register_user,
    project_factory,
    file_factory,
    symbol_factory,
    chunk_factory,
    dependency_factory,
    monkeypatch,
    db_session,
):
    user, headers, project = _create_documentable_project(
        register_user,
        project_factory,
        file_factory,
        symbol_factory,
        chunk_factory,
        dependency_factory,
        "documentation-setup-code@example.com",
    )

    captured = {}

    async def generate_with_setup(prompt, system_prompt=None):
        captured["system_prompt"] = system_prompt

        return (
            "# Project Overview\n"
            "This project greets users.\n\n"
            "## Installation\n"
            "Install the dependencies from "
            "[requirements.txt](requirements.txt).\n\n"
            "```bash\n"
            "pip install -r requirements.txt\n"
            "```\n\n"
            "More details live at <https://example.com/setup>.\n\n"
            "![Screenshot](docs/screenshot.png)\n\n"
            "## Running the Application\n"
            "Start the server with `python app.py`.\n\n"
            "## License\n"
            "This project is licensed under the MIT License.\n\n"
            "## Contributing\n"
            "Read CONTRIBUTING.md first.\n"
        )

    monkeypatch.setattr(
        documentation_service.ollama_service,
        "generate_response",
        generate_with_setup,
    )

    response = client.post(
        f"/api/projects/{project.id}/documentation",
        headers=headers,
    )

    assert response.status_code == 200, response.text

    content = response.json()["content"]

    # Setup commands are preserved in fenced code blocks.
    assert "```bash" in content
    assert "pip install -r requirements.txt" in content
    assert "`python app.py`" in content

    # Links become plain text and images are dropped.
    assert "](requirements.txt)" not in content
    assert "requirements.txt)." not in content
    assert "Install the dependencies from requirements.txt." in content
    assert "https://example.com/setup" in content
    assert "![Screenshot]" not in content
    assert "docs/screenshot.png" not in content

    # Boilerplate sections are removed.
    assert "## License" not in content
    assert "MIT License" not in content
    assert "## Contributing" not in content
    assert "CONTRIBUTING.md" not in content

    stored = (
        db_session.query(Documentation)
        .filter(Documentation.project_id == project.id)
        .one()
    )

    assert stored.content == content

    system_prompt = captured["system_prompt"].lower()

    assert "fenced code blocks" in system_prompt
    assert "markdown links" in system_prompt


def test_legacy_documentation_is_sanitized_on_read(
    client,
    register_user,
    project_factory,
    file_factory,
    symbol_factory,
    chunk_factory,
    dependency_factory,
    db_session,
):
    user, headers, project = _create_documentable_project(
        register_user,
        project_factory,
        file_factory,
        symbol_factory,
        chunk_factory,
        dependency_factory,
        "documentation-sanitize-read@example.com",
    )

    legacy = Documentation(
        project_id=project.id,
        content=(
            "# Project Overview\n"
            "Uses `src/main.py` as documented in "
            "[the guide](https://example.com/guide).\n\n"
            "## Installation\n"
            "```bash\n"
            "pip install -r requirements.txt\n"
            "```\n\n"
            "## Notes\n"
            "Keep this paragraph.\n\n"
            "## License\n"
            "Old license text.\n"
        ),
    )

    db_session.add(legacy)
    db_session.commit()

    response = client.get(
        f"/api/projects/{project.id}/documentation",
        headers=headers,
    )

    assert response.status_code == 200, response.text

    content = response.json()["content"]

    assert "Uses `src/main.py`" in content
    assert "the guide" in content
    assert "](https://example.com/guide)" not in content
    assert "Keep this paragraph." in content
    assert "```bash" in content
    assert "pip install -r requirements.txt" in content
    assert "## License" not in content
    assert "Old license text." not in content

    # The stored record is left untouched; only the response is clean.
    db_session.refresh(legacy)
    assert "## License" in legacy.content


def test_sanitize_documentation_keeps_code_and_strips_links():
    cleaned = documentation_service.sanitize_documentation(
        "# Overview\n"
        "Uses `src/main.py` as the entry point.\n\n"
        "- [Overview](#overview)\n"
        "- [Structure](docs/structure.md)\n\n"
        "## Installation\n"
        "```bash\n"
        "pip install -r requirements.txt\n"
        "```\n"
        "The `src` directory holds the code.\n\n"
        "## Contributing\n"
        "Open a pull request.\n"
    )

    assert "Uses `src/main.py`" in cleaned
    assert "- Overview" in cleaned
    assert "- Structure" in cleaned
    assert "](" not in cleaned
    assert "```bash" in cleaned
    assert "pip install -r requirements.txt" in cleaned
    assert "The `src` directory holds the code." in cleaned
    assert "## Contributing" not in cleaned
    assert "Open a pull request." not in cleaned


def test_documentation_context_includes_project_setup_files(
    client,
    register_user,
    project_factory,
    file_factory,
    symbol_factory,
    chunk_factory,
    dependency_factory,
    fake_documentation_ai,
    db_session,
    tmp_path,
):
    user, headers, project = _create_documentable_project(
        register_user,
        project_factory,
        file_factory,
        symbol_factory,
        chunk_factory,
        dependency_factory,
        "documentation-setup-context@example.com",
    )

    (tmp_path / "requirements.txt").write_text(
        "Flask\ngunicorn\n",
        encoding="utf-8",
    )
    (tmp_path / "Procfile").write_text(
        "web: gunicorn app:app\n",
        encoding="utf-8",
    )
    (tmp_path / "README.md").write_text(
        "# Demo\n\nRun `pip install -r requirements.txt`.\n",
        encoding="utf-8",
    )

    file_factory(
        project.id,
        "requirements.txt",
        language="Other",
    )
    file_factory(project.id, "Procfile", language="Other")
    file_factory(project.id, "README.md", language="Markdown")

    project.root_path = str(tmp_path)
    db_session.commit()

    response = client.post(
        f"/api/projects/{project.id}/documentation",
        headers=headers,
    )

    assert response.status_code == 200, response.text

    prompt = fake_documentation_ai["prompt"]

    assert "PROJECT SETUP AND DEPLOYMENT FILES" in prompt
    assert "File: requirements.txt" in prompt
    assert "gunicorn" in prompt
    assert "File: Procfile" in prompt
    assert "web: gunicorn app:app" in prompt
    assert "File: README.md" in prompt
    assert "pip install -r requirements.txt" in prompt
    assert "only" in prompt.lower()


def test_documentation_requires_authentication(
    client,
    register_user,
    project_factory,
):
    user, _ = register_user("documentation-auth@example.com")
    project = project_factory(user.id, "Auth Documentation")

    response = client.post(f"/api/projects/{project.id}/documentation")

    assert response.status_code == 401
