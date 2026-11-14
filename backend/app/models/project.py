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


class Project(Base):

    __tablename__ = "projects"

    # Unique project ID
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    # User who owns this project
    owner_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Project information
    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    # How the project was imported
    # Allowed values: github, zip, manual
    source_type: Mapped[str] = mapped_column(
        String(20),
        default="manual",
        nullable=False
    )

    # GitHub repository URL, if applicable
    repository_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    # Path where project files are stored
    root_path: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True
    )

    # Project processing status
    # Examples: created, importing, ready, failed
    status: Mapped[str] = mapped_column(
        String(30),
        default="created",
        nullable=False
    )

    # Creation timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Last update timestamp
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Relationship with User
    owner = relationship(
        "User",
        back_populates="projects"
    )

    # Relationship with ProjectFile
    files = relationship(
        "ProjectFile",
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    # Relationship with Dependency
    dependencies = relationship(
        "Dependency",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
