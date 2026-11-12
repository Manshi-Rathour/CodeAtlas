
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.project_file import ProjectFile
from app.services.analysis.file_scanner import scan_project


def save_file_inventory(
    db: Session,
    project: Project
) -> dict:
    """
    Scan an imported project and save its file inventory
    into PostgreSQL.

    Existing inventory records are replaced when rescanning.
    """

    if not project.root_path:
        raise ValueError("Project source directory is not configured.")

    # Scan the project directory
    scan_result = scan_project(project.root_path)

    try:
        # Remove previous inventory before saving fresh results
        db.query(ProjectFile).filter(
            ProjectFile.project_id == project.id
        ).delete(synchronize_session=False)

        # Convert scanner results into database records
        file_records = []

        for file_data in scan_result["files"]:

            file_record = ProjectFile(
                project_id=project.id,
                filename=file_data["filename"],
                relative_path=file_data["relative_path"],
                extension=file_data["extension"],
                language=file_data["language"],
                size_bytes=file_data["size_bytes"]
            )

            file_records.append(file_record)

        # Bulk insert file records
        if file_records:
            db.add_all(file_records)

        # Update project status
        project.status = "ready"

        db.commit()

        return {
            "project_id": project.id,
            "total_files": scan_result["total_files"],
            "language_counts": scan_result["language_counts"],
            "skipped": scan_result["skipped"]
        }

    except Exception:
        db.rollback()
        raise
