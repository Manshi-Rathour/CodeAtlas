import re

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.code_chunk import CodeChunk
from app.models.project_file import ProjectFile


# Expand common developer concepts into related code terms.
RELATED_TERMS = {
    "authentication": [
        "auth", "login", "logout", "token",
        "password", "verify", "authenticate",
    ],
    "authorization": [
        "permission", "role", "access", "authorize",
    ],
    "database": [
        "db", "database", "session", "engine",
        "query", "connection", "repository",
    ],
    "registration": [
        "register", "signup", "create_user",
        "create_account",
    ],
    "api": [
        "route", "endpoint", "router",
        "controller", "request", "response",
    ],
    "error": [
        "exception", "try", "except",
        "raise", "error_handler",
    ],
    "configuration": [
        "config", "settings", "environment",
        "env",
    ],
    "file": [
        "upload", "download", "read",
        "write", "storage",
    ],
}


def search_code_chunks(
    db: Session,
    project_id: int,
    question: str,
    limit: int = 8,
) -> list[dict]:
    """
    Search code chunks using keywords and related
    programming terminology.

    Only searches files belonging to the requested project.
    """

    # Extract unique words from the question.
    original_terms = list(dict.fromkeys(
        term.lower()
        for term in re.findall(
            r"[a-zA-Z_][a-zA-Z0-9_]*",
            question
        )
        if len(term) > 1
    ))

    if not original_terms:
        return []

    # Expand terms using related programming concepts.
    expanded_terms = set(original_terms)

    for term in original_terms:
        for concept, related_words in RELATED_TERMS.items():

            concept_words = [concept] + related_words

            if term in concept_words:
                expanded_terms.update(concept_words)

    terms = list(expanded_terms)[:30]

    # Build database search conditions.
    conditions = []

    for term in terms:
        pattern = f"%{term}%"

        conditions.extend([
            CodeChunk.name.ilike(pattern),
            CodeChunk.content.ilike(pattern),
            ProjectFile.relative_path.ilike(pattern),
        ])

    # Retrieve matching chunks from this project.
    results = (
        db.query(CodeChunk, ProjectFile.relative_path)
        .join(
            ProjectFile,
            CodeChunk.file_id == ProjectFile.id
        )
        .filter(
            ProjectFile.project_id == project_id,
            CodeChunk.content.isnot(None),
            or_(*conditions)
        )
        .all()
    )

    ranked_results = []

    for chunk, file_path in results:

        name = (chunk.name or "").lower()
        path = file_path.lower()
        content = (chunk.content or "").lower()

        # Give more importance to exact original terms.
        original_score = sum(
            name.count(term) * 5
            + path.count(term) * 3
            + content.count(term)
            for term in original_terms
        )

        # Related terms provide additional relevance.
        related_score = sum(
            name.count(term) * 2
            + path.count(term)
            + content.count(term) * 0.5
            for term in terms
            if term not in original_terms
        )

        # Prefer named functions, classes and methods
        # when their names match the original question.
        structure_score = 0

        if chunk.chunk_type in {
            "function", "method", "class"
        } and any(term in name for term in original_terms):
            structure_score = 5

        score = (
            original_score
            + related_score
            + structure_score
        )

        ranked_results.append({
            "file_path": file_path,
            "name": chunk.name,
            "chunk_type": chunk.chunk_type,
            "start_line": chunk.start_line,
            "end_line": chunk.end_line,
            "content": chunk.content,
            "score": score,
        })

    # Sort by relevance, highest score first.
    ranked_results.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    return ranked_results[:limit]
