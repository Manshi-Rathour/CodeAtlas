import sys
from pathlib import Path

import pytest

# Add the backend directory to Python's import path.
BACKEND_DIR = Path(__file__).resolve().parents[1]

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database.connection import get_db
from app.database.base import Base

# Import models so SQLAlchemy registers their tables.
from app.models import (  # noqa: F401
    Chat,
    CodeChunk,
    CodeSymbol,
    Dependency,
    Documentation,
    Project,
    ProjectFile,
    User,
)


TEST_DATABASE_URL = "sqlite://"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    bind=test_engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


@pytest.fixture(scope="session", autouse=True)
def create_test_tables():
    Base.metadata.create_all(bind=test_engine)

    yield

    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session():
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.rollback()
        db.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


# --------------------------------------------------
# PHASE 3 TEST HELPERS
# --------------------------------------------------


@pytest.fixture
def register_user(client, db_session):
    """
    Create a user through the real signup endpoint and return
    the user record plus Authorization headers.
    """

    def _register(email, full_name="Phase 3 Test User"):
        response = client.post(
            "/api/auth/signup",
            json={
                "full_name": full_name,
                "email": email,
                "password": "TestPassword123",
            },
        )

        assert response.status_code == 201, response.text

        user = (
            db_session.query(User)
            .filter(User.email == email)
            .first()
        )

        return user, {
            "Authorization": f"Bearer {response.json()['access_token']}"
        }

    return _register


@pytest.fixture
def project_factory(db_session):
    """Create a project directly in the test database."""

    def _create(owner_id, name="Phase 3 Project"):
        project = Project(
            owner_id=owner_id,
            name=name,
            source_type="manual",
            status="ready",
        )

        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)

        return project

    return _create


@pytest.fixture
def file_factory(db_session):
    """Create a project file directly in the test database."""

    def _create(
        project_id,
        relative_path,
        language="Python",
        filename=None,
    ):
        name = filename or Path(relative_path).name

        project_file = ProjectFile(
            project_id=project_id,
            filename=name,
            relative_path=relative_path,
            extension=Path(relative_path).suffix,
            language=language,
            size_bytes=10,
        )

        db_session.add(project_file)
        db_session.commit()
        db_session.refresh(project_file)

        return project_file

    return _create


@pytest.fixture
def chunk_factory(db_session):
    """Create a code chunk directly in the test database."""

    def _create(
        file_id,
        name="main",
        chunk_type="function",
        content="def main():\n    return 1\n",
        start_line=1,
        end_line=3,
    ):
        chunk = CodeChunk(
            file_id=file_id,
            chunk_type=chunk_type,
            name=name,
            start_line=start_line,
            end_line=end_line,
            content=content,
        )

        db_session.add(chunk)
        db_session.commit()
        db_session.refresh(chunk)

        return chunk

    return _create


@pytest.fixture
def symbol_factory(db_session):
    """Create a code symbol directly in the test database."""

    def _create(
        file_id,
        name="main",
        symbol_type="function",
        start_line=1,
        end_line=3,
        source_code="def main():\n    return 1\n",
    ):
        symbol = CodeSymbol(
            file_id=file_id,
            name=name,
            symbol_type=symbol_type,
            start_line=start_line,
            end_line=end_line,
            source_code=source_code,
        )

        db_session.add(symbol)
        db_session.commit()
        db_session.refresh(symbol)

        return symbol

    return _create


@pytest.fixture
def dependency_factory(db_session):
    """Create a dependency directly in the test database."""

    def _create(
        project_id,
        file_id,
        dependency_name="helpers",
        dependency_type="import",
        line_number=1,
        resolved_file_id=None,
        imported_symbols=None,
    ):
        dependency = Dependency(
            project_id=project_id,
            file_id=file_id,
            resolved_file_id=resolved_file_id,
            dependency_name=dependency_name,
            dependency_type=dependency_type,
            line_number=line_number,
            imported_symbols=imported_symbols,
        )

        db_session.add(dependency)
        db_session.commit()
        db_session.refresh(dependency)

        return dependency

    return _create
