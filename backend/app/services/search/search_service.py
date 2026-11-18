import re

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.code_chunk import CodeChunk
from app.models.project_file import ProjectFile


# Ignore common English words that create noisy search matches.
STOP_WORDS = {
    "the", "and", "for", "are", "was", "were", "what", "which", "who",
    "how", "does", "did", "this", "that", "these", "those", "with",
    "from", "into", "about", "can", "could", "should", "would", "will",
    "you", "your", "please", "explain", "describe", "tell", "show",
    "where", "when", "why", "there", "their", "have", "has", "had",
    "its", "it", "is", "of", "in", "on", "to", "a", "an", "or", "be",
    "me", "my", "mine", "we", "us", "our", "ours", "i", "am",
    "do", "done", "get", "give", "list", "find", "search",
    "present", "currently", "available", "use", "uses", "used",
    "using", "any", "all", "some", "every", "each", "also", "just",
    "only", "inside", "function", "functions", "method", "methods",
    "class", "classes", "file", "files", "code", "codebase",
    "line", "lines", "variable", "variables", "implementation",
    "implemented", "definition", "definitions", "logic",
    "work", "works", "working", "happen", "happens",
}

# Maximum candidate rows fetched before ranking in Python.
MAX_CANDIDATE_ROWS = 500


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
    "sql": [
        "select", "insert", "update", "delete",
        "query", "queries", "table", "database",
    ],
    "queries": [
        "sql", "select", "insert", "update", "delete",
        "query", "table", "database",
    ],
    "frontend": [
        "client", "component", "fetch", "axios",
        "request", "api", "ui",
    ],
    "backend": [
        "server", "route", "endpoint", "controller",
        "handler", "api", "database",
    ],
}


def count_term_matches(text: str, term: str) -> int:
    """
    Count term occurrences at token boundaries.

    Plain substring counts make short words such as "me" match
    "message" or "home", which produces unrelated search results.
    Prefix matching is still allowed so "auth" can match
    "authentication".
    """

    if not text or not term:
        return 0

    pattern = r"(?<![a-z0-9_])" + re.escape(term)

    return len(re.findall(pattern, text))


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

    # Extract unique, meaningful words from the question.
    original_terms = list(dict.fromkeys(
        term.lower()
        for term in re.findall(
            r"[a-zA-Z_][a-zA-Z0-9_]*",
            question
        )
        if len(term) > 1 and term.lower() not in STOP_WORDS
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
        .limit(MAX_CANDIDATE_ROWS)
        .all()
    )

    ranked_results = []
    best_by_location = {}

    for chunk, file_path in results:

        name = (chunk.name or "").lower()
        path = file_path.lower()
        content = (chunk.content or "").lower()

        # Give more importance to exact original terms.
        original_score = sum(
            count_term_matches(name, term) * 5
            + count_term_matches(path, term) * 3
            + count_term_matches(content, term)
            for term in original_terms
        )

        # Related terms provide additional relevance.
        related_score = sum(
            count_term_matches(name, term) * 2
            + count_term_matches(path, term)
            + count_term_matches(content, term) * 0.5
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

        candidate = {
            "file_path": file_path,
            "name": chunk.name,
            "chunk_type": chunk.chunk_type,
            "start_line": chunk.start_line,
            "end_line": chunk.end_line,
            "content": chunk.content,
            "score": score,
        }

        # Keep only the best match for the same code location.
        location = (
            file_path,
            chunk.start_line,
            chunk.end_line,
        )

        existing = best_by_location.get(location)

        if existing is None or score > existing["score"]:
            best_by_location[location] = candidate

    ranked_results = list(best_by_location.values())

    # Sort by relevance, highest score first.
    ranked_results.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    if not ranked_results:
        return []

    top_score = ranked_results[0]["score"]

    if top_score <= 0:
        return []

    # Drop weak matches that are far below the best result. This keeps
    # source references focused on the question instead of returning
    # every chunk that happened to share a common word.
    minimum_score = max(1.0, top_score * 0.35)

    relevant_results = [
        result
        for result in ranked_results
        if result["score"] >= minimum_score
    ]

    return relevant_results[:limit]
