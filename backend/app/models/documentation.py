from datetime import datetime

from sqlalchemy import (
    Integer,
    Text,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    func,
)

from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Documentation(Base):

    __tablename__ = "project_documentations"

    # Unique documentation record ID
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    # Project associated with this documentation
    project_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # AI-generated project documentation in Markdown format
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    # Documentation creation timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Documentation update timestamp
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Each project can have only one documentation record
    __table_args__ = (
        UniqueConstraint(
            "project_id",
            name="uq_project_documentation"
        ),
    )
