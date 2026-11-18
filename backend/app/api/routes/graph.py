from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.database.connection import get_db
from app.models.user import User
from app.services.analysis.dependency_analyzer import (
    build_dependency_graph,
)


router = APIRouter(
    prefix="/api/projects",
    tags=["Dependency Graph"],
)


@router.get("/{project_id}/graph")
def get_project_dependency_graph(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return the internal file dependency graph of a project.

    Nodes are project files. Edges are resolved internal imports.
    """

    try:
        return build_dependency_graph(
            db=db,
            user_id=current_user.id,
            project_id=project_id,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        )

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while building the dependency graph.",
        )
