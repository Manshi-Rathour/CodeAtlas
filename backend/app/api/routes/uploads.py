
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.database.connection import get_db
from app.models.user import User
from app.schemas.project import ProjectResponse
from app.services.source.upload_service import upload_and_extract_project
from app.services.source.import_service import create_imported_project


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
    name: str = Form(..., min_length=2, max_length=150),
    description: str | None = Form(default=None, max_length=2000),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload a ZIP project and save it through the common import service.
    """

    try:
        extracted_path, storage_id = await upload_and_extract_project(
            uploaded_file=file,
            user_id=current_user.id
        )

        project = create_imported_project(
            db=db,
            user_id=current_user.id,
            name=name,
            description=description,
            extracted_path=extracted_path,
            storage_id=storage_id,
            source_type="zip"
        )

        return project

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Project upload failed. Please try again."
        )
