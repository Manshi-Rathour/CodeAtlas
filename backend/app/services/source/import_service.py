
import shutil

from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.project import Project
from app.services.analysis.file_inventory_service import save_file_inventory


def create_imported_project(
    db: Session,
    user_id: int,
    name: str,
    extracted_path: Path,
    storage_id: str,
    source_type: str,
    description: str | None = None,
    repository_url: str | None = None
) -> Project:
    """
    Common import pipeline for ZIP and GitHub projects.

    1. Creates the project record.
    2. Scans the extracted source code.
    3. Saves file inventory in PostgreSQL.
    4. Marks the project as ready.

    Cleans up extracted files if the import fails.
    """

    backend_dir = Path(__file__).resolve().parents[3]

    project_storage = (
        backend_dir
        / settings.UPLOAD_DIR
        / str(user_id)
        / storage_id
    )

    try:
        # Step 1: Create project record
        project = Project(
            owner_id=user_id,
            name=name,
            description=description,
            source_type=source_type,
            repository_url=repository_url,
            root_path=str(extracted_path),
            status="importing"
        )

        db.add(project)

        # Generate project ID without committing
        db.flush()
        db.refresh(project)

        # Step 2, 3 and 4:
        # Scan files, save inventory and mark project ready.
        save_file_inventory(
            db=db,
            project=project
        )

        return project

    except Exception:
        # Roll back pending database changes
        db.rollback()

        # Remove extracted project files
        shutil.rmtree(project_storage, ignore_errors=True)

        raise
