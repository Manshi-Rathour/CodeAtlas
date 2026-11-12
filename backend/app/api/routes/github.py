import logging
import requests

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.database.connection import get_db
from app.models.user import User
from app.schemas.project import ProjectResponse
from app.services.source.github_service import import_github_repository
from app.services.source.import_service import create_imported_project


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/github",
    tags=["GitHub Import"]
)


class GitHubImportRequest(BaseModel):
    repository_url: str = Field(min_length=1, max_length=500)
    branch: str = Field(default="main", min_length=1, max_length=255)
    name: str | None = Field(default=None, min_length=2, max_length=150)
    description: str | None = Field(default=None, max_length=2000)


@router.post(
    "/import",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED
)
def import_github_project(
    request: GitHubImportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        (
            extracted_path,
            storage_id,
            owner,
            repository
        ) = import_github_repository(
            repository_url=request.repository_url,
            user_id=current_user.id,
            branch=request.branch
        )

        project = create_imported_project(
            db=db,
            user_id=current_user.id,
            name=request.name or repository,
            description=request.description,
            extracted_path=extracted_path,
            storage_id=storage_id,
            source_type="github",
            repository_url=request.repository_url
        )

        return project

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )

    except requests.RequestException:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not download the GitHub repository. Please try again."
        )


    except Exception:

        logger.exception("Unexpected error during GitHub project import")

        raise HTTPException(

            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,

            detail="GitHub project import failed. Please try again."

        )
