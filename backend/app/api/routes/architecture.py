from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.api.dependencies import get_current_user

from app.models.user import User

from app.services.architecture.architecture_service import (
    analyze_project_architecture,
)

from app.services.architecture.architecture_explanation_service import (
    prepare_architecture_summary,
    generate_architecture_explanation,
)


router = APIRouter(
    prefix="/api/projects",
    tags=["Project Architecture"],
)


@router.get("/{project_id}/architecture")
async def get_project_architecture(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve structural and AI-generated project architecture."""

    try:
        architecture = analyze_project_architecture(
            db=db,
            user_id=current_user.id,
            project_id=project_id,
        )

        architecture_summary = prepare_architecture_summary(
            architecture
        )

        explanation = await generate_architecture_explanation(
            architecture
        )

        architecture["architecture_summary"] = architecture_summary
        architecture["ai_explanation"] = explanation

        return architecture

    except ValueError as error:
        message = str(error)

        error_status = (
            status.HTTP_404_NOT_FOUND
            if message == "Project not found."
            else status.HTTP_400_BAD_REQUEST
        )

        raise HTTPException(
            status_code=error_status,
            detail=message,
        )

    except RuntimeError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        )

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during architecture analysis.",
        )
