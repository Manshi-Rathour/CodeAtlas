from app.services.analysis.tree_sitter_parser import (
    analyze_source_code,
    normalize_language,
)

from app.services.analysis.symbol_extractor import extract_symbols
from app.services.analysis.chunk_extractor import extract_chunks
from app.services.analysis.dependency_extractor import extract_dependencies


# Convert scanner language names into Tree-sitter grammar names.
LANGUAGE_ALIASES = {
    "c++": "cpp",
    "c": "c",
    "javascript": "javascript",
    "typescript": "typescript",
    "tsx": "tsx",
    "python": "python",
    "java": "java",
    "go": "go",
    "rust": "rust",
    "php": "php",
    "ruby": "ruby",
    "html": "html",
    "css": "css",
    "sql": "sql",
    "swift": "swift",
    "kotlin": "kotlin",
}


def analyze_file(source_code: str, language: str) -> dict:
    """
    Analyze one source file and extract its code symbols,
    chunks, and dependencies.
    """

    # Convert scanner language name into Tree-sitter language name.
    normalized_name = LANGUAGE_ALIASES.get(
        language.lower().strip()
    )

    if normalized_name is None:
        return {
            "language": language,
            "analysis": None,
            "symbols": [],
            "chunks": [],
            "dependencies": [],
            "supported": False,
        }

    # Validate the Tree-sitter language.
    normalized_name = normalize_language(normalized_name)

    # Parse source code.
    analysis_result = analyze_source_code(
        source_code,
        normalized_name
    )

    # Extract standardized symbols.
    symbols = extract_symbols(analysis_result)

    # Extract standardized chunks.
    chunks = extract_chunks(analysis_result)

    # Extract standardized dependencies.
    dependencies = extract_dependencies(
        analysis_result,
        source_code,
    )

    return {
        "language": normalized_name,
        "analysis": analysis_result,
        "symbols": symbols,
        "chunks": chunks,
        "dependencies": dependencies,
        "supported": True,
    }
