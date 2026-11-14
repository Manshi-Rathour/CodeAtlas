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
from app.services.analysis.analysis_service import analyze_project
from app.models.code_symbol import CodeSymbol
from app.models.code_chunk import CodeChunk
from app.models.project_file import ProjectFile
from app.models.dependency import Dependency


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


# --------------------------------------------------
# 6. ANALYZE PROJECT
# --------------------------------------------------

@router.post(
    "/{project_id}/analyze"
)
def analyze_project_endpoint(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    # Verify project ownership.
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id
    ).first()

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found."
        )

    try:
        # Run project-wide code analysis.
        result = analyze_project(
            db,
            project
        )

        return {
            "message": "Project analysis completed successfully.",
            "analysis": result
        }

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Project analysis failed."
        )


# --------------------------------------------------
# 7. GET PROJECT ANALYSIS RESULTS
# --------------------------------------------------

@router.get(
    "/{project_id}/analysis"
)
def get_project_analysis(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    # Verify project ownership.
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id
    ).first()

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found."
        )

    # Retrieve project files.
    project_files = db.query(ProjectFile).filter(
        ProjectFile.project_id == project_id
    ).all()

    file_map = {
        file.id: file.relative_path
        for file in project_files
    }

    # Retrieve code symbols.
    symbols = db.query(CodeSymbol).filter(
        CodeSymbol.file_id.in_(file_map.keys())
    ).all()

    # Retrieve code chunks.
    chunks = db.query(CodeChunk).filter(
        CodeChunk.file_id.in_(file_map.keys())
    ).all()

    # Retrieve dependencies.
    dependencies = db.query(Dependency).filter(
        Dependency.project_id == project_id
    ).all()

    return {
        "project_id": project_id,

        "total_symbols": len(symbols),
        "total_chunks": len(chunks),
        "total_dependencies": len(dependencies),

        "symbols": [
            {
                "id": symbol.id,
                "file": file_map.get(symbol.file_id),
                "name": symbol.name,
                "type": symbol.symbol_type,
                "start_line": symbol.start_line,
                "end_line": symbol.end_line,
                "source_code": symbol.source_code,
            }
            for symbol in symbols
        ],

        "chunks": [
            {
                "id": chunk.id,
                "file": file_map.get(chunk.file_id),
                "name": chunk.name,
                "type": chunk.chunk_type,
                "start_line": chunk.start_line,
                "end_line": chunk.end_line,
                "content": chunk.content,
            }
            for chunk in chunks
        ],

        "dependencies": [
            {
                "id": dependency.id,
                "file": file_map.get(dependency.file_id),
                "name": dependency.dependency_name,
                "type": dependency.dependency_type,
                "line_number": dependency.line_number,
                "imported_symbols": dependency.imported_symbols,
                "resolved_file": file_map.get(dependency.resolved_file_id),
            }
            for dependency in dependencies
        ],
    }