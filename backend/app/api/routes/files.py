from math import ceil

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.api.dependencies import get_current_user

from app.models.user import User
from app.models.project import Project
from app.models.project_file import ProjectFile

from app.schemas.project_file import (
    ProjectFileListResponse,
    ProjectFileTreeResponse,
)

from pathlib import Path

from app.services.analysis.file_scanner import (
    is_binary_file,
    is_sensitive_file,
)

router = APIRouter(
    prefix="/api/projects",
    tags=["Project Files"]
)

# Upper bound for the folder tree payload. Keeps very large repositories
# responsive in the browser while still showing the real structure.
MAX_TREE_FILES = 2000


def _owned_project(
    db: Session,
    project_id: int,
    current_user: User,
) -> Project:
    """Return the project only when it belongs to the current user."""

    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id
    ).first()

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found."
        )

    return project


def _project_files_query(
    db: Session,
    project_id: int,
    language: str | None = None,
    search: str | None = None,
):
    """Build the filtered project file query used by list and tree views."""

    files_query = db.query(ProjectFile).filter(
        ProjectFile.project_id == project_id
    )

    if language:
        files_query = files_query.filter(
            func.lower(ProjectFile.language) == language.strip().lower()
        )

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

    return files_query


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

    _owned_project(db, project_id, current_user)

    # 2. Build the filtered file query.

    files_query = _project_files_query(
        db,
        project_id,
        language,
        search,
    )

    # 3. Count matching files before pagination.

    total_files = files_query.count()

    # 4. Calculate pagination information.

    total_pages = ceil(total_files / page_size) if total_files else 0

    # 5. Fetch only the requested page.

    files = files_query.order_by(
        ProjectFile.relative_path.asc()
    ).offset(
        (page - 1) * page_size
    ).limit(
        page_size
    ).all()

    # 6. Return the paginated response.

    return {
        "total": total_files,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "files": files
    }


@router.get(
    "/{project_id}/file-tree",
    response_model=ProjectFileTreeResponse
)
def get_project_file_tree(
    project_id: int,

    language: str | None = Query(default=None, min_length=1, max_length=100),
    search: str | None = Query(default=None, min_length=1, max_length=200),

    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Return every matching project file in one response.

    The browser groups the flat paths into folders so the explorer can
    show the real directory structure instead of a paginated file list.
    """

    # 1. Verify that the project belongs to the logged-in user.

    _owned_project(db, project_id, current_user)

    # 2. Build the filtered file query.

    files_query = _project_files_query(
        db,
        project_id,
        language,
        search,
    )

    total_files = files_query.count()

    # 3. Fetch the files, bounded so huge repositories stay responsive.

    files = files_query.order_by(
        ProjectFile.relative_path.asc()
    ).limit(
        MAX_TREE_FILES
    ).all()

    return {
        "total": total_files,
        "shown": len(files),
        "truncated": total_files > len(files),
        "files": files,
    }


@router.get("/{project_id}/files/{file_id}/content")
def get_project_file_content(
    project_id: int,
    file_id: int,

    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Verify project ownership.

    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id
    ).first()

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found."
        )

    # 2. Find the requested file inside this project.

    project_file = db.query(ProjectFile).filter(
        ProjectFile.id == file_id,
        ProjectFile.project_id == project_id
    ).first()

    if project_file is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found."
        )

    # 3. Verify project storage exists.

    if not project.root_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project storage is unavailable."
        )

    try:
        root = Path(project.root_path).resolve(strict=True)

        if not root.is_dir():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project directory not found."
            )

        # 4. Resolve the requested relative path safely.

        candidate = root / project_file.relative_path

        if candidate.is_symlink():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Symbolic links cannot be accessed."
            )

        file_path = candidate.resolve(strict=True)

        if not file_path.is_relative_to(root):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access outside the project directory is forbidden."
            )

        if not file_path.is_file():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File does not exist."
            )

        # 5. Apply the scanner's security restrictions again.

        if is_sensitive_file(file_path.name):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sensitive files cannot be accessed."
            )

        max_file_size = 2 * 1024 * 1024

        if file_path.stat().st_size > max_file_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File exceeds the 2 MB reading limit."
            )

        if is_binary_file(file_path):
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="Binary files cannot be displayed."
            )

        # 6. Read a limited amount of source code.

        with file_path.open("rb") as file:
            content_bytes = file.read(max_file_size + 1)

        if len(content_bytes) > max_file_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File exceeds the 2 MB reading limit."
            )

        content = content_bytes.decode("utf-8")

        # 7. Return file information and source code.

        return {
            "id": project_file.id,
            "project_id": project_file.project_id,
            "filename": project_file.filename,
            "relative_path": project_file.relative_path,
            "extension": project_file.extension,
            "language": project_file.language,
            "size_bytes": len(content_bytes),
            "content": content
        }

    except HTTPException:
        raise

    except (OSError, UnicodeDecodeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to safely read this file."
        )