from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.chat import Chat
from app.models.code_chunk import CodeChunk
from app.models.code_symbol import CodeSymbol
from app.models.dependency import Dependency
from app.models.documentation import Documentation
from app.models.project import Project
from app.models.project_file import ProjectFile
from app.services.analysis.api_detector import (
    detect_project_api_endpoints,
)


def _symbol_metrics(db: Session, file_ids: list[int]) -> dict:
    if not file_ids:
        return {
            "total": 0,
            "functions": 0,
            "methods": 0,
            "classes": 0,
            "other": 0,
            "files_with_symbols": 0,
        }

    rows = (
        db.query(
            CodeSymbol.symbol_type,
            func.count(CodeSymbol.id),
        )
        .filter(CodeSymbol.file_id.in_(file_ids))
        .group_by(CodeSymbol.symbol_type)
        .all()
    )

    counts = {
        (symbol_type or "other").lower(): count
        for symbol_type, count in rows
    }

    total = sum(counts.values())

    functions = counts.get("function", 0)
    methods = counts.get("method", 0)
    classes = counts.get("class", 0)
    other = max(total - functions - methods - classes, 0)

    files_with_symbols = (
        db.query(func.count(func.distinct(CodeSymbol.file_id)))
        .filter(CodeSymbol.file_id.in_(file_ids))
        .scalar()
        or 0
    )

    return {
        "total": total,
        "functions": functions,
        "methods": methods,
        "classes": classes,
        "other": other,
        "files_with_symbols": files_with_symbols,
    }


def _language_metrics(project_files: list[ProjectFile]) -> list[dict]:
    languages: dict[str, dict] = {}

    for project_file in project_files:
        language = project_file.language or "Other"
        entry = languages.setdefault(
            language,
            {"language": language, "files": 0, "bytes": 0},
        )

        entry["files"] += 1
        entry["bytes"] += project_file.size_bytes or 0

    return sorted(
        languages.values(),
        key=lambda item: (-item["files"], item["language"]),
    )


def build_project_metrics(
    db: Session,
    project_id: int,
) -> dict:
    """
    Build project metrics from stored analysis records.

    Every value is derived from PostgreSQL or the recorded source
    directory. Imported code is never executed.
    """

    project = db.query(Project).filter(
        Project.id == project_id
    ).first()

    if not project:
        raise ValueError("Project not found.")

    project_files = (
        db.query(ProjectFile)
        .filter(ProjectFile.project_id == project_id)
        .all()
    )

    file_ids = [project_file.id for project_file in project_files]
    total_bytes = sum(
        project_file.size_bytes or 0
        for project_file in project_files
    )

    symbol_metrics = _symbol_metrics(db, file_ids)

    if file_ids:
        chunk_count = (
            db.query(func.count(CodeChunk.id))
            .filter(CodeChunk.file_id.in_(file_ids))
            .scalar()
            or 0
        )
        files_with_chunks = (
            db.query(func.count(func.distinct(CodeChunk.file_id)))
            .filter(CodeChunk.file_id.in_(file_ids))
            .scalar()
            or 0
        )
    else:
        chunk_count = 0
        files_with_chunks = 0

    dependency_rows = (
        db.query(Dependency)
        .filter(Dependency.project_id == project_id)
        .all()
    )

    resolved_dependencies = sum(
        1 for dependency in dependency_rows
        if dependency.resolved_file_id is not None
    )

    documentation = (
        db.query(Documentation)
        .filter(Documentation.project_id == project_id)
        .first()
    )

    conversation_count = (
        db.query(func.count(func.distinct(Chat.conversation_id)))
        .filter(
            Chat.project_id == project_id,
            Chat.user_id == project.owner_id,
        )
        .scalar()
        or 0
    )

    api_result = detect_project_api_endpoints(
        db=db,
        project_id=project_id,
    )

    return {
        "project_id": project.id,
        "project_name": project.name,
        "status": project.status,
        "total_files": len(project_files),
        "total_bytes": total_bytes,
        "languages": _language_metrics(project_files),
        "symbols": symbol_metrics,
        "chunks": {
            "total": chunk_count,
            "files_with_chunks": files_with_chunks,
        },
        "dependencies": {
            "total": len(dependency_rows),
            "resolved": resolved_dependencies,
            "external": len(dependency_rows) - resolved_dependencies,
        },
        "api_endpoints": api_result["total"],
        "api_frameworks": api_result["frameworks"],
        "conversations": conversation_count,
        "documentation": {
            "exists": documentation is not None,
            "updated_at": (
                documentation.updated_at
                if documentation is not None
                else None
            ),
        },
    }
