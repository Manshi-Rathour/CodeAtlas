import uuid

from sqlalchemy.orm import Session

from app.models.chat import Chat
from app.models.project import Project

from app.services.search.search_service import search_code_chunks

from app.services.ai.ollama_service import ollama_service

from app.services.ai.prompt_builder import (
    build_codebase_system_prompt,
    build_codebase_prompt,
)


MAX_CONTEXT_CHARS = 12000


def build_code_context(
    retrieved_chunks: list[dict],
) -> tuple[str, list[dict]]:
    """
    Build a limited code context and matching source references.
    """

    context_parts = []
    sources = []
    seen_sources = set()
    used_content = set()
    total_chars = 0

    for chunk in retrieved_chunks:

        content = chunk.get("content") or ""

        if not content.strip():
            continue

        # Avoid including identical source code repeatedly.
        if content in used_content:
            continue

        context_part = f"""
File: {chunk['file_path']}
Structure: {chunk['chunk_type']} - {chunk['name']}
Lines: {chunk['start_line']}-{chunk['end_line']}

Source code:
{content}
"""

        # Do not exceed the context size limit.
        if total_chars + len(context_part) > MAX_CONTEXT_CHARS:
            continue

        context_parts.append(context_part)
        total_chars += len(context_part)

        source_key = (
            chunk["file_path"],
            chunk["start_line"],
            chunk["end_line"],
        )

        if source_key not in seen_sources:
            sources.append({
                "file_path": chunk["file_path"],
                "start_line": chunk["start_line"],
                "end_line": chunk["end_line"],
                "chunk_type": chunk["chunk_type"],
                "name": chunk["name"],
            })

            seen_sources.add(source_key)

        used_content.add(content)

    if not context_parts:
        return (
            "No relevant source code chunks were found for this question.",
            [],
        )

    return "\n".join(context_parts), sources


async def process_chat_message(
    db: Session,
    user_id: int,
    project_id: int,
    question: str,
    conversation_id: str | None = None,
) -> dict:
    """
    Process a user's codebase question.

    1. Verify project ownership.
    2. Retrieve relevant code.
    3. Build limited AI context.
    4. Generate an answer using Ollama.
    5. Save conversation messages.
    """

    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == user_id,
    ).first()

    if not project:
        raise ValueError("Project not found.")

    if not conversation_id:
        conversation_id = str(uuid.uuid4())

    else:
        existing_message = db.query(Chat).filter(
            Chat.conversation_id == conversation_id,
            Chat.user_id == user_id,
            Chat.project_id == project_id,
        ).first()

        if not existing_message:
            raise ValueError("Conversation not found.")

    try:

        # Retrieve previous messages from this conversation.
        conversation_history = (
            db.query(Chat)
            .filter(
                Chat.conversation_id == conversation_id,
                Chat.user_id == user_id,
                Chat.project_id == project_id,
            )
            .order_by(Chat.created_at.desc(), Chat.id.desc())
            .limit(10)
            .all()
        )

        # Reverse messages to restore chronological order.
        conversation_history.reverse()

        history = [
            {
                "role": message.role,
                "content": message.content,
            }
            for message in conversation_history
        ]

        retrieved_chunks = search_code_chunks(
            db=db,
            project_id=project_id,
            question=question,
        )

        code_context, sources = build_code_context(
            retrieved_chunks
        )

        system_prompt = build_codebase_system_prompt()

        prompt = build_codebase_prompt(
            question=question,
            code_context=code_context,
            conversation_history=history,
        )

        answer = await ollama_service.generate_response(
            prompt=prompt,
            system_prompt=system_prompt,
        )

        if not answer:
            raise RuntimeError(
                "The AI returned an empty response."
            )

        user_message = Chat(
            conversation_id=conversation_id,
            user_id=user_id,
            project_id=project_id,
            role="user",
            content=question,
        )

        assistant_message = Chat(
            conversation_id=conversation_id,
            user_id=user_id,
            project_id=project_id,
            role="assistant",
            content=answer,
            sources=sources,
        )

        db.add(user_message)
        db.add(assistant_message)

        db.commit()

        return {
            "conversation_id": conversation_id,
            "answer": answer,
            "sources": sources,
        }

    except Exception:
        db.rollback()
        raise


def get_project_conversations(
    db: Session,
    user_id: int,
    project_id: int,
) -> list[dict]:
    """
    Retrieve all conversations belonging to a user's project.
    """

    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == user_id
    ).first()

    if not project:
        raise ValueError("Project not found.")

    messages = (
        db.query(Chat)
        .filter(
            Chat.project_id == project_id,
            Chat.user_id == user_id
        )
        .order_by(Chat.created_at.asc(), Chat.id.asc())
        .all()
    )

    conversations = {}

    for message in messages:
        conversation_id = message.conversation_id

        if conversation_id not in conversations:
            conversations[conversation_id] = {
                "conversation_id": conversation_id,
                "project_id": project_id,
                "title": "",
                "message_count": 0,
                "created_at": message.created_at,
                "updated_at": message.created_at,
            }

        conversation = conversations[conversation_id]

        conversation["message_count"] += 1
        conversation["updated_at"] = message.created_at

        if message.role == "user" and not conversation["title"]:
            conversation["title"] = message.content[:100]

    return sorted(
        conversations.values(),
        key=lambda item: item["updated_at"],
        reverse=True
    )


def get_conversation_messages(
    db: Session,
    user_id: int,
    project_id: int,
    conversation_id: str,
) -> list[Chat]:
    """
    Retrieve all messages from a specific conversation.
    """

    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == user_id
    ).first()

    if not project:
        raise ValueError("Project not found.")

    messages = (
        db.query(Chat)
        .filter(
            Chat.conversation_id == conversation_id,
            Chat.user_id == user_id,
            Chat.project_id == project_id
        )
        .order_by(Chat.created_at.asc(), Chat.id.asc())
        .all()
    )

    if not messages:
        raise ValueError("Conversation not found.")

    return messages