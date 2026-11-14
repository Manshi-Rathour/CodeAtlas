from datetime import datetime

from sqlalchemy import (
    Integer,
    String,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    Index,
    func
)

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class ProjectFile(Base):

    __tablename__ = "project_files"

    # Unique file record ID
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    # Project to which this file belongs
    project_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Original filename
    filename: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )

    # Relative path inside the project
    relative_path: Mapped[str] = mapped_column(
        String(2000),
        nullable=False
    )

    # File extension
    extension: Mapped[str] = mapped_column(
        String(30),
        default="",
        nullable=False
    )

    # Detected programming language
    language: Mapped[str] = mapped_column(
        String(100),
        default="Other",
        nullable=False,
        index=True
    )

    # File size in bytes
    size_bytes: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    # Record creation timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationship with Project
    project = relationship(
        "Project",
        back_populates="files"
    )

    # Relationship with CodeSymbol
    symbols = relationship(
        "CodeSymbol",
        back_populates="file",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    # Relationship with CodeChunk
    chunks = relationship(
        "CodeChunk",
        back_populates="file",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    # Relationship with Dependency
    dependencies = relationship(
        "Dependency",
        back_populates="file",
        foreign_keys="Dependency.file_id",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    # Prevent duplicate file paths within the same project
    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "relative_path",
            name="uq_project_file_path"
        ),
        Index(
            "ix_project_files_project_language",
            "project_id",
            "language"
        ),
    )
