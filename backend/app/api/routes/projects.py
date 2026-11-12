
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.user import User
from app.models.project import Project
from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse
)
from app.api.dependencies import get_current_user


router = APIRouter(
    prefix="/api/projects",
    tags=["Projects"]
)


# --------------------------------------------------
# 1. CREATE PROJECT
# --------------------------------------------------

@router.post(
    "/",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED
)
def create_project(
    project_data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    project_name = project_data.name.strip()

    if len(project_name) < 2:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Project name must contain at least 2 characters."
        )

    new_project = Project(
        owner_id=current_user.id,
        name=project_name,
        description=project_data.description,
        source_type=project_data.source_type,
        repository_url=project_data.repository_url,
        status="created"
    )

    db.add(new_project)
    db.commit()
    db.refresh(new_project)

    return new_project


# --------------------------------------------------
# 2. GET ALL PROJECTS OF CURRENT USER
# --------------------------------------------------

@router.get(
    "/",
    response_model=list[ProjectResponse]
)
def get_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    projects = db.query(Project).filter(
        Project.owner_id == current_user.id
    ).order_by(
        Project.created_at.desc()
    ).all()

    return projects


# --------------------------------------------------
# 3. GET PROJECT BY ID
# --------------------------------------------------

@router.get(
    "/{project_id}",
    response_model=ProjectResponse
)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

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


# --------------------------------------------------
# 4. UPDATE PROJECT
# --------------------------------------------------

@router.patch(
    "/{project_id}",
    response_model=ProjectResponse
)
def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id
    ).first()

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found."
        )

    update_data = project_data.model_dump(
        exclude_unset=True
    )

    if "name" in update_data:

        if update_data["name"] is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Project name cannot be null."
            )

        update_data["name"] = update_data["name"].strip()

        if len(update_data["name"]) < 2:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Project name must contain at least 2 characters."
            )

    for field, value in update_data.items():
        setattr(project, field, value)

    db.commit()
    db.refresh(project)

    return project


# --------------------------------------------------
# 5. DELETE PROJECT
# --------------------------------------------------

@router.delete(
    "/{project_id}"
)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id
    ).first()

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found."
        )

    db.delete(project)
    db.commit()

    return {
        "message": "Project deleted successfully.",
        "project_id": project_id
    }
