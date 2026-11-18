from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.api.dependencies import get_current_user

from app.models.user import User
from app.models.project import Project
from app.models.documentation import Documentation

from app.schemas.documentation import (
    DocumentationResponse,
    DocumentationStatusResponse,
)

from app.services.documentation.documentation_service import (
    generate_project_documentation,
    sanitize_documentation,
)


router = APIRouter(
    prefix="/api/projects",
    tags=["Project Documentation"]
)


@router.post(
    "/{project_id}/documentation",
    response_model=DocumentationResponse
)
async def generate_documentation(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate AI documentation for a project."""

    try:
        documentation = await generate_project_documentation(
            db=db,
            user_id=current_user.id,
            project_id=project_id,
        )

        return documentation

    except ValueError as error:
        message = str(error)

        error_status = (
            status.HTTP_404_NOT_FOUND
            if message == "Project not found."
            else status.HTTP_400_BAD_REQUEST
        )

        raise HTTPException(
            status_code=error_status,
            detail=message
        )

    except RuntimeError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error)
        )

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while generating documentation."
        )


@router.get(
    "/{project_id}/documentation",
    response_model=DocumentationResponse
)
def get_documentation(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve previously generated project documentation."""

    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id
    ).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found."
        )

    documentation = db.query(Documentation).filter(
        Documentation.project_id == project_id
    ).first()

    if not documentation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documentation has not been generated yet."
        )

    # Older records may contain Markdown links from previous prompts.
    # Sanitize on read so broken links are never shown in the app.
    return DocumentationResponse(
        id=documentation.id,
        project_id=documentation.project_id,
        content=sanitize_documentation(documentation.content),
        created_at=documentation.created_at,
        updated_at=documentation.updated_at,
    )


@router.get(
    "/{project_id}/documentation/status",
    response_model=DocumentationStatusResponse
)
def get_documentation_status(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check whether project documentation exists."""

    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id
    ).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found."
        )

    documentation = db.query(Documentation).filter(
        Documentation.project_id == project_id
    ).first()

    return {
        "project_id": project_id,
        "exists": documentation is not None,
        "message": (
            "Documentation is available."
            if documentation
            else "Documentation has not been generated yet."
        )
    }
