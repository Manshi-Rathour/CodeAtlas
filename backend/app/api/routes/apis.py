from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.database.connection import get_db
from app.models.project import Project
from app.models.user import User

from app.schemas.analysis import (
    ApiEndpointListResponse,
    ProjectMetricsResponse,
)
from app.services.analysis.api_detector import (
    detect_project_api_endpoints,
)
from app.services.analysis.metrics_service import build_project_metrics


router = APIRouter(
    prefix="/api/projects",
    tags=["Project APIs and Metrics"],
)


def _verify_ownership(
    db: Session,
    project_id: int,
    current_user: User,
) -> None:
    project = db.query(Project.id).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id,
    ).first()

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        )


@router.get(
    "/{project_id}/apis",
    response_model=ApiEndpointListResponse,
)
def get_project_apis(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return HTTP API endpoints detected in the project source code.

    The detector reads source text only and never executes imported code.
    """

    _verify_ownership(db, project_id, current_user)

    try:
        return detect_project_api_endpoints(
            db=db,
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
            detail="Unable to detect API endpoints for this project.",
        )


@router.get(
    "/{project_id}/metrics",
    response_model=ProjectMetricsResponse,
)
def get_project_metrics(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return file, symbol, dependency, API and activity metrics.
    """

    _verify_ownership(db, project_id, current_user)

    try:
        return build_project_metrics(
            db=db,
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
            detail="Unable to build metrics for this project.",
        )
