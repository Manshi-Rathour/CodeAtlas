from datetime import datetime

from sqlalchemy import (
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    JSON,
    Index,
    func,
)

from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Chat(Base):

    __tablename__ = "chats"

    # Unique message ID
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    # Conversation ID groups messages belonging to one chat
    conversation_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        index=True
    )

    # User who owns this conversation
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Project being discussed
    project_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Message sender: user or assistant
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    # Actual message content
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    # Source files and line references used in the answer
    sources: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True
    )

    # Message creation timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Index for retrieving a conversation's messages in order
    __table_args__ = (
        Index(
            "ix_chats_conversation_created",
            "conversation_id",
            "created_at"
        ),
    )
