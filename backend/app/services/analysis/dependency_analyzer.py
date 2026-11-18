from sqlalchemy.orm import Session

from app.models.dependency import Dependency
from app.models.project import Project
from app.models.project_file import ProjectFile


def build_dependency_graph(
    db: Session,
    user_id: int,
    project_id: int,
) -> dict:
    """
    Build a directed file dependency graph for a project.

    Nodes represent project files and edges represent resolved
    internal dependencies. External and unresolved imports are
    ignored because they do not point at a project file.

    Returns structured data derived entirely from PostgreSQL records.
    """

    # Verify project ownership before exposing any graph data.
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == user_id,
    ).first()

    if not project:
        raise ValueError("Project not found.")

    # Every project file is a potential node, including isolated files.
    project_files = (
        db.query(ProjectFile)
        .filter(ProjectFile.project_id == project_id)
        .order_by(ProjectFile.relative_path.asc())
        .all()
    )

    nodes = [
        {
            "id": project_file.id,
            "label": project_file.filename,
            "file_path": project_file.relative_path,
            "language": project_file.language or "Other",
        }
        for project_file in project_files
    ]

    file_ids = {project_file.id for project_file in project_files}

    # Only resolved internal dependencies become graph edges.
    dependencies = (
        db.query(Dependency)
        .filter(
            Dependency.project_id == project_id,
            Dependency.resolved_file_id.isnot(None),
        )
        .order_by(Dependency.id.asc())
        .all()
    )

    edges = []
    seen_edges = set()

    for dependency in dependencies:

        source_id = dependency.file_id
        target_id = dependency.resolved_file_id

        # Ignore dangling references and self-imports.
        if source_id not in file_ids:
            continue

        if target_id not in file_ids:
            continue

        if source_id == target_id:
            continue

        # Remove exact duplicates while preserving legitimate
        # multiple imports between the same pair of files.
        edge_key = (
            source_id,
            target_id,
            dependency.dependency_name,
            dependency.dependency_type,
            dependency.line_number,
        )

        if edge_key in seen_edges:
            continue

        seen_edges.add(edge_key)

        edges.append({
            "id": dependency.id,
            "source": source_id,
            "target": target_id,
            "dependency": dependency.dependency_name,
            "type": dependency.dependency_type,
            "line_number": dependency.line_number,
        })

    return {
        "project_id": project.id,
        "project_name": project.name,
        "nodes": nodes,
        "edges": edges,
        "total_nodes": len(nodes),
        "total_edges": len(edges),
    }
