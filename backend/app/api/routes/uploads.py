
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.config import settings
from app.database.connection import get_db
from app.models.project import Project
from app.models.user import User
from app.schemas.project import ProjectResponse
from app.services.source.upload_service import upload_and_extract_project


router = APIRouter(
    prefix="/api/uploads",
    tags=["Project Uploads"]
)


@router.post(
    "/zip",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED
)
async def upload_zip_project(
    name: str,
    description: str | None = None,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload and extract a ZIP project.
    The project is associated with the authenticated user.
    """

    extracted_project = None
    storage_id = None

    try:
        extracted_project, storage_id = await upload_and_extract_project(
            uploaded_file=file,
            user_id=current_user.id
        )

        project = Project(
            owner_id=current_user.id,
            name=name,
            description=description,
            source_type="zip",
            root_path=str(extracted_project),
            status="imported"
        )

        db.add(project)
        db.commit()
        db.refresh(project)

        return project

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )

    except Exception:
        db.rollback()

        # Remove extracted files if database creation fails.
        if extracted_project is not None:
            import shutil

            storage_directory = extracted_project.parent
            shutil.rmtree(storage_directory, ignore_errors=True)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Project upload failed. Please try again."
        )
