from pathlib import Path

from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.project_file import ProjectFile
from app.models.code_symbol import CodeSymbol
from app.models.code_chunk import CodeChunk
from app.models.dependency import Dependency

from app.services.analysis.parser_manager import analyze_file
from app.services.analysis.dependency_resolver import resolve_dependencies

from app.services.analysis.file_scanner import (
    is_binary_file,
    is_sensitive_file,
)


MAX_FILE_SIZE = 2 * 1024 * 1024


def analyze_project(
    db: Session,
    project: Project
) -> dict:
    """
    Analyze all supported source files in a project
    and save extracted symbols into PostgreSQL.
    """

    if not project.root_path:
        raise ValueError("Project source directory is not configured.")

    # Resolve the project directory safely.
    root = Path(project.root_path).resolve(strict=True)

    if not root.is_dir():
        raise ValueError("Project directory does not exist.")

    # Retrieve all registered project files.
    project_files = db.query(ProjectFile).filter(
        ProjectFile.project_id == project.id
    ).all()

    # Remove symbols from previous analysis.
    db.query(CodeSymbol).filter(
        CodeSymbol.file_id.in_(
            db.query(ProjectFile.id).filter(
                ProjectFile.project_id == project.id
            )
        )
    ).delete(synchronize_session=False)

    # Remove chunks from previous analysis.
    db.query(CodeChunk).filter(
        CodeChunk.file_id.in_(
            db.query(ProjectFile.id).filter(
                ProjectFile.project_id == project.id
            )
        )
    ).delete(synchronize_session=False)

    # Remove dependencies from previous analysis.
    db.query(Dependency).filter(
        Dependency.project_id == project.id
    ).delete(synchronize_session=False)

    total_analyzed = 0
    total_skipped = 0
    total_symbols = 0
    total_chunks = 0
    total_dependencies = 0
    created_dependencies = []

    try:

        for project_file in project_files:

            try:
                # Skip sensitive files.
                if is_sensitive_file(project_file.filename):
                    total_skipped += 1
                    continue

                # Resolve the file path.
                candidate = root / project_file.relative_path

                if candidate.is_symlink():
                    total_skipped += 1
                    continue

                file_path = candidate.resolve(strict=True)

                # Prevent directory traversal.
                if not file_path.is_relative_to(root):
                    total_skipped += 1
                    continue

                if not file_path.is_file():
                    total_skipped += 1
                    continue

                # Enforce the file size limit.
                if file_path.stat().st_size > MAX_FILE_SIZE:
                    total_skipped += 1
                    continue

                # Skip binary files.
                if is_binary_file(file_path):
                    total_skipped += 1
                    continue

                # Read source code.
                with file_path.open("rb") as file:
                    content_bytes = file.read(MAX_FILE_SIZE + 1)

                if len(content_bytes) > MAX_FILE_SIZE:
                    total_skipped += 1
                    continue

                source_code = content_bytes.decode("utf-8")

                # Parse the file and extract symbols.
                result = analyze_file(
                    source_code,
                    project_file.language
                )

                # Skip unsupported languages.
                if not result["supported"]:
                    total_skipped += 1
                    continue

                # Save extracted symbols.
                for symbol in result["symbols"]:

                    code_symbol = CodeSymbol(
                        file_id=project_file.id,
                        name=symbol["name"],
                        symbol_type=symbol["symbol_type"],
                        start_line=symbol["start_line"],
                        end_line=symbol["end_line"],
                        source_code=symbol["source_code"],
                    )

                    db.add(code_symbol)
                    total_symbols += 1

                # Save extracted chunks.
                for chunk in result["chunks"]:
                    code_chunk = CodeChunk(
                        file_id=project_file.id,
                        name=chunk["name"],
                        chunk_type=chunk["chunk_type"],
                        start_line=chunk["start_line"],
                        end_line=chunk["end_line"],
                        content=chunk["content"],
                    )

                    db.add(code_chunk)
                    total_chunks += 1

                # Save extracted dependencies.
                for dependency in result["dependencies"]:

                    code_dependency = Dependency(
                        project_id=project.id,
                        file_id=project_file.id,
                        dependency_name=dependency["dependency_name"],
                        dependency_type=dependency["dependency_type"],
                        line_number=dependency["line_number"],
                        imported_symbols=dependency["imported_symbols"],
                    )

                    db.add(code_dependency)
                    created_dependencies.append(code_dependency)
                    total_dependencies += 1

                total_analyzed += 1

            except (OSError, UnicodeDecodeError, ValueError):
                # One problematic file should not stop
                # analysis of the remaining project files.
                total_skipped += 1
                continue

        # Resolve local dependencies after all files are analyzed.
        # Use the newly created objects directly: the session is configured
        # with autoflush=False, so querying before a flush would return an
        # empty result set and nothing would ever be resolved.
        resolved_dependencies = resolve_dependencies(
            created_dependencies,
            project_files
        )

        # Save symbols, chunks and resolved dependencies.
        db.commit()

        return {
            "project_id": project.id,
            "total_files": len(project_files),
            "analyzed_files": total_analyzed,
            "skipped_files": total_skipped,
            "total_symbols": total_symbols,
            "total_chunks": total_chunks,
            "total_dependencies": total_dependencies,
            "resolved_dependencies": resolved_dependencies,
        }

    except Exception:
        db.rollback()
        raise
