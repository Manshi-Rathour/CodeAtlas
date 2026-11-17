from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.api.dependencies import get_current_user

from app.models.user import User

from app.services.ai.chat_service import (
    process_chat_message,
    get_project_conversations,
    get_conversation_messages,
)

from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ChatConversationResponse,
    ChatMessageResponse,
)


router = APIRouter(
    prefix="/api/projects",
    tags=["AI Chat"]
)


@router.post(
    "/{project_id}/chat",
    response_model=ChatResponse
)
async def chat_with_codebase(
    project_id: int,
    chat_data: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Ask questions about a specific project using AI.
    """

    try:
        result = await process_chat_message(
            db=db,
            user_id=current_user.id,
            project_id=project_id,
            question=chat_data.question,
            conversation_id=chat_data.conversation_id
        )

        return result

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error)
        )

    except RuntimeError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error)
        )

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing your question."
        )


@router.get(
    "/{project_id}/chats",
    response_model=list[ChatConversationResponse]
)
def get_chats(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve all conversations for a project."""

    try:
        return get_project_conversations(
            db=db,
            user_id=current_user.id,
            project_id=project_id
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error)
        )


@router.get(
    "/{project_id}/chats/{conversation_id}",
    response_model=list[ChatMessageResponse]
)
def get_chat_messages(
    project_id: int,
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve all messages from a conversation."""

    try:
        messages = get_conversation_messages(
            db=db,
            user_id=current_user.id,
            project_id=project_id,
            conversation_id=conversation_id
        )

        return [
            {
                "id": message.id,
                "conversation_id": message.conversation_id,
                "project_id": message.project_id,
                "role": message.role,
                "content": message.content,
                "sources": message.sources or [],
                "created_at": message.created_at,
            }
            for message in messages
        ]

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error)
        )