import pytest

from app.models.chat import Chat
from app.services.ai import chat_service


@pytest.fixture
def fake_ollama(monkeypatch):
    """Replace local Ollama inference with a deterministic fake."""

    captured = {}

    async def fake_generate(prompt, system_prompt=None):
        captured["prompt"] = prompt
        captured["system_prompt"] = system_prompt
        return "The main function starts the application."

    monkeypatch.setattr(
        chat_service.ollama_service,
        "generate_response",
        fake_generate,
    )

    return captured


def _create_chunked_project(
    register_user,
    project_factory,
    file_factory,
    chunk_factory,
    email,
):
    user, headers = register_user(email)
    project = project_factory(user.id, "Chat Project")

    main = file_factory(project.id, "src/main.py")

    chunk_factory(
        main.id,
        name="main",
        content="def main():\n    print('hello')\n",
        start_line=1,
        end_line=2,
    )

    return user, headers, project


def test_new_conversation_returns_answer_and_sources(
    client,
    register_user,
    project_factory,
    file_factory,
    chunk_factory,
    fake_ollama,
):
    user, headers, project = _create_chunked_project(
        register_user,
        project_factory,
        file_factory,
        chunk_factory,
        "chat-new@example.com",
    )

    response = client.post(
        f"/api/projects/{project.id}/chat",
        headers=headers,
        json={"question": "What does the main function do?"},
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["conversation_id"]
    assert data["answer"] == "The main function starts the application."
    assert len(data["sources"]) == 1
    assert data["sources"][0]["file_path"] == "src/main.py"

    # The system prompt is always supplied separately.
    assert "untrusted" in fake_ollama["system_prompt"].lower()

    # Source code is wrapped in clearly delimited reference context.
    assert "CODEBASE CONTEXT" in fake_ollama["prompt"]
    assert "What does the main function do?" in fake_ollama["prompt"]


def test_messages_are_persisted_and_retrievable(
    client,
    register_user,
    project_factory,
    file_factory,
    chunk_factory,
    fake_ollama,
    db_session,
):
    user, headers, project = _create_chunked_project(
        register_user,
        project_factory,
        file_factory,
        chunk_factory,
        "chat-persist@example.com",
    )

    response = client.post(
        f"/api/projects/{project.id}/chat",
        headers=headers,
        json={"question": "Explain main."},
    )

    conversation_id = response.json()["conversation_id"]

    stored = (
        db_session.query(Chat)
        .filter(Chat.conversation_id == conversation_id)
        .order_by(Chat.id.asc())
        .all()
    )

    assert [message.role for message in stored] == ["user", "assistant"]
    assert stored[0].content == "Explain main."
    assert stored[1].sources

    list_response = client.get(
        f"/api/projects/{project.id}/chats",
        headers=headers,
    )

    assert list_response.status_code == 200

    conversations = list_response.json()

    assert len(conversations) == 1
    assert conversations[0]["conversation_id"] == conversation_id
    assert conversations[0]["message_count"] == 2
    assert conversations[0]["title"] == "Explain main."

    messages_response = client.get(
        f"/api/projects/{project.id}/chats/{conversation_id}",
        headers=headers,
    )

    assert messages_response.status_code == 200

    messages = messages_response.json()

    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"


def test_follow_up_question_includes_conversation_history(
    client,
    register_user,
    project_factory,
    file_factory,
    chunk_factory,
    fake_ollama,
):
    user, headers, project = _create_chunked_project(
        register_user,
        project_factory,
        file_factory,
        chunk_factory,
        "chat-followup@example.com",
    )

    first = client.post(
        f"/api/projects/{project.id}/chat",
        headers=headers,
        json={"question": "What does main do?"},
    )

    conversation_id = first.json()["conversation_id"]

    second = client.post(
        f"/api/projects/{project.id}/chat",
        headers=headers,
        json={
            "question": "What does it return?",
            "conversation_id": conversation_id,
        },
    )

    assert second.status_code == 200
    assert second.json()["conversation_id"] == conversation_id

    prompt = fake_ollama["prompt"]

    assert "PREVIOUS CONVERSATION" in prompt
    assert "What does main do?" in prompt
    assert "What does it return?" in prompt


def test_chat_handles_missing_relevant_context(
    client,
    register_user,
    project_factory,
    file_factory,
    fake_ollama,
):
    user, headers = register_user("chat-nocontext@example.com")
    project = project_factory(user.id, "No Context Project")
    file_factory(project.id, "src/main.py")

    response = client.post(
        f"/api/projects/{project.id}/chat",
        headers=headers,
        json={"question": "Where is authentication implemented?"},
    )

    assert response.status_code == 200

    prompt = fake_ollama["prompt"]

    assert "No relevant source code chunks were found" in prompt
    assert "insufficient" in prompt.lower()


def test_conversation_is_isolated_per_user(
    client,
    register_user,
    project_factory,
    file_factory,
    chunk_factory,
    fake_ollama,
):
    owner, owner_headers, project = _create_chunked_project(
        register_user,
        project_factory,
        file_factory,
        chunk_factory,
        "chat-owner@example.com",
    )

    _, other_headers = register_user("chat-intruder@example.com")

    conversation = client.post(
        f"/api/projects/{project.id}/chat",
        headers=owner_headers,
        json={"question": "Explain main."},
    ).json()

    # Another user cannot list the project's conversations.
    list_response = client.get(
        f"/api/projects/{project.id}/chats",
        headers=other_headers,
    )

    assert list_response.status_code == 404

    # Another user cannot read the conversation.
    messages_response = client.get(
        f"/api/projects/{project.id}/chats/{conversation['conversation_id']}",
        headers=other_headers,
    )

    assert messages_response.status_code == 404

    # Another user cannot continue the conversation.
    follow_up = client.post(
        f"/api/projects/{project.id}/chat",
        headers=other_headers,
        json={
            "question": "Continue.",
            "conversation_id": conversation["conversation_id"],
        },
    )

    assert follow_up.status_code == 404


def test_conversation_id_cannot_be_reused_across_projects(
    client,
    register_user,
    project_factory,
    file_factory,
    chunk_factory,
    fake_ollama,
):
    user, headers = register_user("chat-crossproject@example.com")

    first_project = project_factory(user.id, "First Chat Project")
    second_project = project_factory(user.id, "Second Chat Project")

    for project, path in (
        (first_project, "a.py"),
        (second_project, "b.py"),
    ):
        project_file = file_factory(project.id, path)
        chunk_factory(project_file.id, name="run")

    conversation = client.post(
        f"/api/projects/{first_project.id}/chat",
        headers=headers,
        json={"question": "Explain run."},
    ).json()

    response = client.post(
        f"/api/projects/{second_project.id}/chat",
        headers=headers,
        json={
            "question": "Explain run here.",
            "conversation_id": conversation["conversation_id"],
        },
    )

    assert response.status_code == 404


def test_chat_returns_503_when_ollama_fails(
    client,
    register_user,
    project_factory,
    file_factory,
    chunk_factory,
    monkeypatch,
    db_session,
):
    user, headers, project = _create_chunked_project(
        register_user,
        project_factory,
        file_factory,
        chunk_factory,
        "chat-offline@example.com",
    )

    async def failing_generate(prompt, system_prompt=None):
        raise RuntimeError(
            "Could not connect to Ollama. Make sure Ollama is running."
        )

    monkeypatch.setattr(
        chat_service.ollama_service,
        "generate_response",
        failing_generate,
    )

    response = client.post(
        f"/api/projects/{project.id}/chat",
        headers=headers,
        json={"question": "Explain main."},
    )

    assert response.status_code == 503
    assert "Ollama" in response.json()["detail"]

    # Failed requests must not leave partial conversation data behind.
    assert db_session.query(Chat).filter(
        Chat.project_id == project.id
    ).count() == 0


def test_chat_returns_503_for_empty_ai_response(
    client,
    register_user,
    project_factory,
    file_factory,
    chunk_factory,
    monkeypatch,
):
    user, headers, project = _create_chunked_project(
        register_user,
        project_factory,
        file_factory,
        chunk_factory,
        "chat-empty@example.com",
    )

    async def empty_generate(prompt, system_prompt=None):
        return ""

    monkeypatch.setattr(
        chat_service.ollama_service,
        "generate_response",
        empty_generate,
    )

    response = client.post(
        f"/api/projects/{project.id}/chat",
        headers=headers,
        json={"question": "Explain main."},
    )

    assert response.status_code == 503


def test_chat_requires_authentication(client, register_user, project_factory):
    user, _ = register_user("chat-auth@example.com")
    project = project_factory(user.id, "Auth Chat Project")

    response = client.post(
        f"/api/projects/{project.id}/chat",
        json={"question": "Explain the project."},
    )

    assert response.status_code == 401


def test_client_generated_conversation_id_starts_one_conversation(
    client,
    register_user,
    project_factory,
    file_factory,
    chunk_factory,
    fake_ollama,
    db_session,
):
    import uuid

    user, headers, project = _create_chunked_project(
        register_user,
        project_factory,
        file_factory,
        chunk_factory,
        "chat-client-id@example.com",
    )

    conversation_id = str(uuid.uuid4())

    # The frontend sends the same ID again after a dropped response.
    for question in ("Explain main.", "Explain main."):
        response = client.post(
            f"/api/projects/{project.id}/chat",
            headers=headers,
            json={
                "question": question,
                "conversation_id": conversation_id,
            },
        )

        assert response.status_code == 200, response.text
        assert response.json()["conversation_id"] == conversation_id

    conversations = client.get(
        f"/api/projects/{project.id}/chats",
        headers=headers,
    ).json()

    assert len(conversations) == 1
    assert conversations[0]["conversation_id"] == conversation_id
    assert conversations[0]["message_count"] == 4


def test_unknown_non_uuid_conversation_id_returns_404(
    client,
    register_user,
    project_factory,
    file_factory,
    chunk_factory,
    fake_ollama,
):
    user, headers, project = _create_chunked_project(
        register_user,
        project_factory,
        file_factory,
        chunk_factory,
        "chat-invalid-id@example.com",
    )

    response = client.post(
        f"/api/projects/{project.id}/chat",
        headers=headers,
        json={
            "question": "Explain main.",
            "conversation_id": "not-a-conversation",
        },
    )

    assert response.status_code == 404
