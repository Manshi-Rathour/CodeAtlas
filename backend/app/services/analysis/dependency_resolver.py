import posixpath
from pathlib import PurePosixPath

from app.models.dependency import Dependency
from app.models.project_file import ProjectFile


# Languages whose module specifiers can point at another project file.
JAVASCRIPT_LANGUAGES = {
    "javascript",
    "typescript",
    "jsx",
    "tsx",
}

# Extensions tried when a JavaScript/TypeScript import omits one.
JAVASCRIPT_EXTENSIONS = (
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".mjs",
    ".cjs",
    ".mts",
    ".cts",
    ".json",
    ".css",
    ".scss",
    ".sass",
    ".less",
    ".vue",
    ".svelte",
)


def _normalize_path(path: str) -> str:
    """
    Normalize a project-relative POSIX path.

    Collapses "." and ".." segments and strips a leading "./", so paths
    such as "src/components/../utils/format" match "src/utils/format".
    """

    normalized = posixpath.normpath(path.replace("\\", "/"))

    if normalized.startswith("./"):
        normalized = normalized[2:]

    return normalized


def _build_file_lookup(
    project_files: list[ProjectFile],
) -> tuple[dict[str, int], dict[str, int]]:
    """
    Index project files by normalized path.

    A case-insensitive index is built as a fallback because filesystems on
    macOS and Windows are case-insensitive, while recorded paths keep their
    original casing.
    """

    file_lookup: dict[str, int] = {}
    file_lookup_lower: dict[str, int] = {}

    for project_file in project_files:
        if not project_file.relative_path:
            continue

        path = _normalize_path(project_file.relative_path)

        file_lookup.setdefault(path, project_file.id)
        file_lookup_lower.setdefault(path.lower(), project_file.id)

    return file_lookup, file_lookup_lower


def _build_python_module_lookup(
    file_lookup: dict[str, int],
) -> dict[str, int]:
    """
    Index Python modules by their dotted import name.

    Every suffix of a path is registered, so a project whose root is not the
    package root (for example "backend/app/services/auth.py") still resolves
    "app.services.auth" and "services.auth".
    """

    module_lookup: dict[str, int] = {}

    for path, file_id in file_lookup.items():
        if not path.endswith(".py"):
            continue

        parts = path[: -len(".py")].split("/")

        if parts and parts[-1] == "__init__":
            parts = parts[:-1]

        for index in range(len(parts)):
            module_name = ".".join(parts[index:])

            if module_name:
                module_lookup.setdefault(module_name, file_id)

    return module_lookup


def _python_candidates(
    dependency_name: str,
    source_path: PurePosixPath,
) -> list[str]:
    """
    Build candidate project paths for a Python import.

    Handles absolute imports ("app.services.auth") and relative imports
    ("from .models import X", "from ..utils import Y").
    """

    candidates = []

    leading_dots = len(dependency_name) - len(
        dependency_name.lstrip(".")
    )
    module = dependency_name[leading_dots:]

    if leading_dots:
        # Relative imports are resolved from the importing module's package.
        base_path = source_path.parent

        for _ in range(leading_dots - 1):
            base_path = base_path.parent

        base = "" if str(base_path) == "." else str(base_path)
    else:
        base = ""

    module_path = module.replace(".", "/")
    target = (
        posixpath.join(base, module_path)
        if base and module_path
        else (base or module_path)
    )

    if module_path:
        candidates.append(f"{target}.py")
        candidates.append(f"{target}/__init__.py")
    elif base:
        candidates.append(f"{base}/__init__.py")

    return candidates


def _javascript_candidates(
    dependency_name: str,
    source_path: PurePosixPath,
) -> list[str]:
    """
    Build candidate project paths for a local JavaScript/TypeScript import.

    Only relative and root-relative specifiers are local; bare package names
    are external and deliberately left unresolved.
    """

    if dependency_name.startswith("/"):
        base_path = dependency_name.lstrip("/")
    else:
        base_path = str(source_path.parent / dependency_name)

    base = _normalize_path(base_path)

    if not base:
        return []

    candidates = [base]

    for extension in JAVASCRIPT_EXTENSIONS:
        candidates.append(base + extension)

    for extension in JAVASCRIPT_EXTENSIONS:
        candidates.append(posixpath.join(base, "index" + extension))

    return candidates


def _first_match(
    candidates: list[str],
    file_lookup: dict[str, int],
    file_lookup_lower: dict[str, int],
) -> int | None:
    """Return the ID of the first candidate that exists in the project."""

    for candidate in candidates:
        resolved_id = file_lookup.get(
            _normalize_path(candidate)
        )

        if resolved_id is not None:
            return resolved_id

    # Fall back to a case-insensitive comparison.
    for candidate in candidates:
        resolved_id = file_lookup_lower.get(
            _normalize_path(candidate).lower()
        )

        if resolved_id is not None:
            return resolved_id

    return None


def resolve_dependencies(
    dependencies: list[Dependency],
    project_files: list[ProjectFile],
) -> int:
    """
    Resolve local Python and JavaScript/TypeScript
    dependencies to files within the same project.

    External packages remain unresolved.
    """

    file_lookup, file_lookup_lower = _build_file_lookup(project_files)
    python_module_lookup = _build_python_module_lookup(file_lookup)

    files_by_id = {
        project_file.id: project_file
        for project_file in project_files
    }

    resolved_count = 0

    for dependency in dependencies:

        # Reset any previous resolution.
        dependency.resolved_file_id = None

        source_file = files_by_id.get(dependency.file_id)

        if source_file is None:
            continue

        source_path = PurePosixPath(
            _normalize_path(source_file.relative_path)
        )

        language = (source_file.language or "").lower()
        dependency_name = dependency.dependency_name

        candidates: list[str] = []

        if language == "python":
            candidates = _python_candidates(
                dependency_name,
                source_path
            )

            # Absolute imports may be written without the project's
            # leading directory segments.
            resolved_id = _first_match(
                candidates,
                file_lookup,
                file_lookup_lower,
            )

            if resolved_id is None:
                leading_dots = len(dependency_name) - len(
                    dependency_name.lstrip(".")
                )

                if not leading_dots:
                    resolved_id = python_module_lookup.get(
                        dependency_name
                    )

            if resolved_id is not None:
                dependency.resolved_file_id = resolved_id
                resolved_count += 1

            continue

        if language in JAVASCRIPT_LANGUAGES:

            # Bare package names (react, axios, ...) are external.
            if not dependency_name.startswith((".", "/")):
                continue

            candidates = _javascript_candidates(
                dependency_name,
                source_path
            )

        else:
            continue

        resolved_id = _first_match(
            candidates,
            file_lookup,
            file_lookup_lower,
        )

        if resolved_id is not None:
            dependency.resolved_file_id = resolved_id
            resolved_count += 1

    return resolved_count
