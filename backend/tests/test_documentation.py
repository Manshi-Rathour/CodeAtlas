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


def test_documentation_removes_code_examples(
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
        "documentation-code-examples@example.com",
    )

    captured = {}

    async def generate_with_code(prompt, system_prompt=None):
        captured["system_prompt"] = system_prompt

        return (
            "# Project Overview\n"
            "This project greets users.\n\n"
            "## Code Examples\n"
            "```python\n"
            "def main():\n"
            "    return helper()\n"
            "```\n\n"
            "## Important Classes and Functions\n"
            "`main` in `src/main.py` delegates to the helper.\n\n"
            "```js\n"
            "console.log('example')\n"
            "```\n\n"
            "## Dependencies\n"
            "The project imports the helpers module.\n"
        )

    monkeypatch.setattr(
        documentation_service.ollama_service,
        "generate_response",
        generate_with_code,
    )

    response = client.post(
        f"/api/projects/{project.id}/documentation",
        headers=headers,
    )

    assert response.status_code == 200, response.text

    content = response.json()["content"]

    assert "# Project Overview" in content
    assert "## Important Classes and Functions" in content
    assert "## Dependencies" in content
    assert "`main` in `src/main.py`" in content

    # No fenced code blocks and no code example section.
    assert "```" not in content
    assert "Code Examples" not in content
    assert "def main()" not in content
    assert "console.log" not in content

    stored = (
        db_session.query(Documentation)
        .filter(Documentation.project_id == project.id)
        .one()
    )

    assert stored.content == content

    system_prompt = captured["system_prompt"].lower()

    assert "code examples" in system_prompt
    assert "fenced code" in system_prompt


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
            "Uses `src/main.py`.\n\n"
            "## Code Examples\n"
            "An old code example.\n\n"
            "```python\n"
            "print('legacy')\n"
            "```\n\n"
            "## Notes\n"
            "Keep this paragraph.\n"
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

    assert "Uses `src/main.py`." in content
    assert "Keep this paragraph." in content
    assert "Code Examples" not in content
    assert "code example" not in content.lower()
    assert "legacy" not in content
    assert "```" not in content

    # The stored record is left untouched; only the response is clean.
    db_session.refresh(legacy)
    assert "```" in legacy.content


def test_remove_code_examples_keeps_prose_and_inline_code():
    cleaned = documentation_service.remove_code_examples(
        "# Overview\n"
        "Uses `src/main.py` as the entry point.\n\n"
        "- [Overview](#overview)\n"
        "- [Code Examples](#code-examples)\n"
        "3. **Code Examples**\n"
        "- [Structure](#structure)\n\n"
        "## Example Usage\n"
        "Run the app after installing dependencies.\n\n"
        "## Structure\n"
        "```text\nsrc/main.py\n```\n"
        "The `src` directory holds the code.\n"
        "This guide includes code examples.\n"
    )

    assert "Uses `src/main.py`" in cleaned
    assert "[Overview](#overview)" in cleaned
    assert "[Structure](#structure)" in cleaned
    assert "The `src` directory holds the code." in cleaned
    assert "This guide includes" not in cleaned
    assert "Example Usage" not in cleaned
    assert "Code Examples" not in cleaned
    assert "```" not in cleaned
    assert "src/main.py\n```" not in cleaned


def test_documentation_requires_authentication(
    client,
    register_user,
    project_factory,
):
    user, _ = register_user("documentation-auth@example.com")
    project = project_factory(user.id, "Auth Documentation")

    response = client.post(f"/api/projects/{project.id}/documentation")

    assert response.status_code == 401
