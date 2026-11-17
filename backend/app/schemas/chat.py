from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ChatRequest(BaseModel):
    """
    Data received when a user sends a message.
    """

    question: str = Field(
        min_length=1,
        max_length=5000
    )

    conversation_id: str | None = None


class ChatSource(BaseModel):
    """
    Reference to a source file used in an AI response.
    """

    file_path: str
    start_line: int
    end_line: int
    chunk_type: str | None = None
    name: str | None = None


class ChatMessageResponse(BaseModel):
    """
    Represents one stored chat message.
    """

    id: int
    conversation_id: str
    project_id: int
    role: str
    content: str
    sources: list[ChatSource] = Field(default_factory=list)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatResponse(BaseModel):
    """
    Response returned after processing a chat question.
    """

    conversation_id: str
    answer: str
    sources: list[ChatSource] = Field(default_factory=list)


class ChatConversationResponse(BaseModel):
    conversation_id: str
    project_id: int
    title: str
    message_count: int
    created_at: datetime
    updated_at: datetime
