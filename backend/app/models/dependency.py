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


class Dependency(Base):

    __tablename__ = "dependencies"

    # Unique dependency record ID
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    # Project containing this dependency
    project_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # File containing the import statement
    file_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("project_files.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Project file resolved by this dependency, if available
    resolved_file_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("project_files.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Imported module or package name
    dependency_name: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        index=True
    )

    # Type of dependency: import, include, require, etc.
    dependency_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    # Line where the dependency is imported
    line_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    # Imported symbols, if available
    imported_symbols: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # File containing the import statement
    file = relationship(
        "ProjectFile",
        back_populates="dependencies",
        foreign_keys=[file_id]
    )

    # Internal project file resolved by this dependency
    resolved_file = relationship(
        "ProjectFile",
        foreign_keys=[resolved_file_id]
    )
