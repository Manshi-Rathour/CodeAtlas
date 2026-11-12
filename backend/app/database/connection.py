from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings


# Create SQLAlchemy database engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=False
)


# Create a session factory
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)


# Database dependency for FastAPI routes
def get_db() -> Generator[Session, None, None]:

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()
