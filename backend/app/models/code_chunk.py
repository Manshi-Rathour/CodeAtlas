from datetime import datetime

from sqlalchemy import (
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    func,
)

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class CodeChunk(Base):

    __tablename__ = "code_chunks"

    # Unique chunk ID
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    # File containing this code chunk
    file_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("project_files.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Type of structure
    # Examples: html_tag, css_selector, sql_statement
    chunk_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True
    )

    # Name of the structure
    # Examples: div, .container, CREATE TABLE
    name: Mapped[str] = mapped_column(
        String(300),
        nullable=False,
        index=True
    )

    # Starting line in the source file
    start_line: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    # Ending line in the source file
    end_line: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    # Actual source code
    content: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    # Record creation time
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationship with ProjectFile
    file = relationship(
        "ProjectFile",
        back_populates="chunks"
    )
