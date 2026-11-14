from datetime import datetime

from sqlalchemy import (
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    func
)

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class CodeSymbol(Base):

    __tablename__ = "code_symbols"

    # Unique symbol ID
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    # File in which this symbol was found
    file_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("project_files.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Symbol name: login, User, calculate_total
    name: Mapped[str] = mapped_column(
        String(300),
        nullable=False,
        index=True
    )

    # Symbol type: function, method, class, struct, etc.
    symbol_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )

    # Line where the symbol starts
    start_line: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    # Line where the symbol ends
    end_line: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    # Actual source code of the symbol
    source_code: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    # Record creation timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationship with ProjectFile
    file = relationship(
        "ProjectFile",
        back_populates="symbols"
    )
