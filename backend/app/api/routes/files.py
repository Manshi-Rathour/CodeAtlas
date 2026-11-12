
from math import ceil

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.api.dependencies import get_current_user

from app.models.user import User
from app.models.project import Project
from app.models.project_file import ProjectFile

from app.schemas.project_file import ProjectFileListResponse


router = APIRouter(
    prefix="/api/projects",
    tags=["Project Files"]
)


@router.get(
    "/{project_id}/files",
    response_model=ProjectFileListResponse
)
def get_project_files(
    project_id: int,

    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),

    language: str | None = Query(default=None, min_length=1, max_length=100),
    search: str | None = Query(default=None, min_length=1, max_length=200),

    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Verify that the project belongs to the logged-in user.

    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id
    ).first()

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found."
        )

    # 2. Start querying files belonging to this project.

    files_query = db.query(ProjectFile).filter(
        ProjectFile.project_id == project_id
    )

    # 3. Apply language filter if provided.

    if language:
        files_query = files_query.filter(
            func.lower(ProjectFile.language) == language.strip().lower()
        )

    # 4. Search by filename or relative path.

    if search:
        search_term = search.strip()

        files_query = files_query.filter(
            or_(
                ProjectFile.filename.ilike(
                    f"%{search_term}%",
                    escape="\\"
                ),
                ProjectFile.relative_path.ilike(
                    f"%{search_term}%",
                    escape="\\"
                )
            )
        )

    # 5. Count matching files before pagination.

    total_files = files_query.count()

    # 6. Calculate pagination information.

    total_pages = ceil(total_files / page_size) if total_files else 0

    # 7. Fetch only the requested page.

    files = files_query.order_by(
        ProjectFile.relative_path.asc()
    ).offset(
        (page - 1) * page_size
    ).limit(
        page_size
    ).all()

    # 8. Return the paginated response.

    return {
        "total": total_files,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "files": files
    }
