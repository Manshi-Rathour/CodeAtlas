from collections import defaultdict
from pathlib import PurePosixPath

from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.project_file import ProjectFile
from app.models.code_symbol import CodeSymbol
from app.models.dependency import Dependency
from app.services.analysis.file_scanner import NON_PROGRAMMING_FILE_TYPES


def analyze_project_architecture(
    db: Session,
    user_id: int,
    project_id: int,
) -> dict:
    """
    Analyze project structure, modules, symbols and
    internal file dependencies.
    """

    # Verify project ownership
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == user_id,
    ).first()

    if not project:
        raise ValueError("Project not found.")

    # Retrieve project files
    files = (
        db.query(ProjectFile)
        .filter(ProjectFile.project_id == project_id)
        .order_by(ProjectFile.relative_path.asc())
        .all()
    )

    if not files:
        raise ValueError("No project files were found.")

    # Retrieve code symbols
    symbols = (
        db.query(CodeSymbol)
        .join(
            ProjectFile,
            CodeSymbol.file_id == ProjectFile.id,
        )
        .filter(ProjectFile.project_id == project_id)
        .order_by(CodeSymbol.start_line.asc())
        .all()
    )

    # Retrieve all dependencies, then use resolved ones for relationships.
    dependencies = (
        db.query(Dependency)
        .filter(Dependency.project_id == project_id)
        .order_by(Dependency.id.asc())
        .all()
    )

    # Create a file lookup
    file_lookup = {
        project_file.id: project_file
        for project_file in files
    }

    # Group symbols by file
    symbols_by_file = defaultdict(list)

    for symbol in symbols:

        project_file = file_lookup.get(symbol.file_id)

        if not project_file:
            continue

        symbols_by_file[symbol.file_id].append({
            "name": symbol.name,
            "type": symbol.symbol_type,
            "file_path": project_file.relative_path,
            "start_line": symbol.start_line,
            "end_line": symbol.end_line,
        })

    # Build file-level dependency relationships
    file_relationships = []

    # Group relationships between directories
    module_relationships = defaultdict(int)

    for dependency in dependencies:

        if dependency.resolved_file_id is None:
            continue

        source_file = file_lookup.get(dependency.file_id)
        target_file = file_lookup.get(dependency.resolved_file_id)

        if not source_file or not target_file:
            continue

        source_directory = str(
            PurePosixPath(source_file.relative_path).parent
        )

        target_directory = str(
            PurePosixPath(target_file.relative_path).parent
        )

        if source_directory == ".":
            source_directory = "root"

        if target_directory == ".":
            target_directory = "root"

        file_relationships.append({
            "source": source_file.relative_path,
            "target": target_file.relative_path,
            "dependency": dependency.dependency_name,
            "type": dependency.dependency_type,
            "line_number": dependency.line_number,
        })

        if source_directory != target_directory:
            key = (source_directory, target_directory)
            module_relationships[key] += 1

    # Build module summaries
    modules = {}

    for project_file in files:

        path = PurePosixPath(project_file.relative_path)
        directory = str(path.parent)

        if directory == ".":
            directory = "root"

        if directory not in modules:
            modules[directory] = {
                "name": directory,
                "file_count": 0,
                "languages": set(),
                "files": [],
                "symbols": [],
            }

        module = modules[directory]

        module["file_count"] += 1

        if project_file.language not in NON_PROGRAMMING_FILE_TYPES:
            module["languages"].add(project_file.language)

        module["files"].append(project_file.relative_path)

        module["symbols"].extend(
            symbols_by_file.get(project_file.id, [])
        )

    # Convert sets into JSON-friendly lists
    module_list = []

    for module in modules.values():
        module_list.append({
            "name": module["name"],
            "file_count": module["file_count"],
            "languages": sorted(module["languages"]),
            "files": module["files"],
            "symbols": module["symbols"],
        })

    # Convert module relationships
    module_relationship_list = [
        {
            "source": source,
            "target": target,
            "dependency_count": count,
        }
        for (source, target), count
        in module_relationships.items()
    ]

    # Summarize programming languages used across the project.
    language_counts = defaultdict(int)

    for project_file in files:
        language = project_file.language or "Other"

        if language in NON_PROGRAMMING_FILE_TYPES:
            continue

        language_counts[language] += 1

    language_list = [
        {
            "language": language,
            "file_count": count,
        }
        for language, count in sorted(language_counts.items())
    ]

    return {
        "project_id": project_id,
        "project_name": project.name,
        "total_files": len(files),
        "total_symbols": len(symbols),
        "total_dependencies": len(dependencies),
        "total_internal_dependencies": len(file_relationships),
        "languages": language_list,
        "modules": module_list,
        "file_relationships": file_relationships,
        "module_relationships": module_relationship_list,
    }
