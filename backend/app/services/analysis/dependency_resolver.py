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

JAVA_LANGUAGES = {
    "java",
    "kotlin",
    "scala",
}

C_LANGUAGES = {
    "c",
    "c++",
    "cpp",
}

# Languages whose files reference other assets (CSS, JS, templates).
MARKUP_LANGUAGES = {
    "html",
    "htm",
}

STYLESHEET_LANGUAGES = {
    "css",
}

# Package prefixes that always refer to external platforms/libraries.
JAVA_EXTERNAL_PREFIXES = (
    "java.",
    "javax.",
    "kotlin.",
    "kotlinx.",
    "android.",
    "androidx.",
    "junit.",
    "org.junit.",
    "org.mockito.",
)

# Rust crates shipped with the toolchain, never project files.
RUST_EXTERNAL_PREFIXES = (
    "std",
    "core",
    "alloc",
    "proc_macro",
)

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

# Extensions tried for C/C++ includes.
C_EXTENSIONS = (
    "",
    ".h",
    ".hpp",
    ".hh",
    ".hxx",
    ".c",
    ".cc",
    ".cpp",
    ".cxx",
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


def _add_suffix_keys(
    index: dict[str, int],
    path: str,
    file_id: int,
    separator: str,
    lowercase: bool = False,
    min_segments: int = 1,
) -> None:
    """
    Register every suffix of a path in a lookup.

    This lets an import resolve when the project root is not the package
    root, for example "app.services.auth" against
    "backend/app/services/auth.py".
    """

    parts = [part for part in path.split(separator) if part]

    for index_start in range(len(parts)):
        if len(parts) - index_start < min_segments:
            continue

        key = separator.join(parts[index_start:])

        if lowercase:
            key = key.lower()

        index.setdefault(key, file_id)


class _ProjectIndex:
    """Lookup tables built once per dependency resolution pass."""

    def __init__(self, project_files: list[ProjectFile]):
        self.by_id = {
            project_file.id: project_file
            for project_file in project_files
        }

        self.files: dict[str, int] = {}
        self.files_lower: dict[str, int] = {}
        self.path_suffixes: dict[str, int] = {}
        self.directories: dict[str, int] = {}

        # Language-specific module/class indexes.
        self.python_modules: dict[str, int] = {}
        self.java_classes: dict[str, int] = {}
        self.rust_modules: dict[str, int] = {}
        self.php_classes: dict[str, int] = {}
        self.ruby_modules: dict[str, int] = {}

        for project_file in project_files:
            if not project_file.relative_path:
                continue

            path = _normalize_path(project_file.relative_path)
            file_id = project_file.id
            lower_path = path.lower()

            self.files.setdefault(path, file_id)
            self.files_lower.setdefault(lower_path, file_id)
            _add_suffix_keys(
                self.path_suffixes,
                path,
                file_id,
                "/",
            )

            directory = posixpath.dirname(path)

            if lower_path.endswith(".py"):
                module_path = path[: -len(".py")]
                parts = module_path.split("/")

                if parts and parts[-1] == "__init__":
                    parts = parts[:-1]

                for start in range(len(parts)):
                    module_name = ".".join(parts[start:])

                    if module_name:
                        self.python_modules.setdefault(module_name, file_id)

            if lower_path.endswith(".go"):
                # Go imports packages (directories), not individual files.
                if directory:
                    self.directories.setdefault(directory, file_id)

            if lower_path.endswith((".java", ".kt", ".kts")):
                class_path = path.rsplit(".", 1)[0]
                _add_suffix_keys(
                    self.java_classes,
                    class_path,
                    file_id,
                    "/",
                    lowercase=True,
                    min_segments=2,
                )

            if lower_path.endswith(".rs"):
                module_path = path[: -len(".rs")]

                if module_path.endswith("/mod"):
                    module_path = module_path[: -len("/mod")]

                parts = module_path.split("/")

                if parts and parts[0] == "src":
                    parts = parts[1:]

                _add_suffix_keys(
                    self.rust_modules,
                    "/".join(parts),
                    file_id,
                    "/",
                )

            if lower_path.endswith(".php"):
                class_path = path[: -len(".php")]
                _add_suffix_keys(
                    self.php_classes,
                    class_path,
                    file_id,
                    "/",
                    lowercase=True,
                    min_segments=2,
                )

            if lower_path.endswith(".rb"):
                module_path = path[: -len(".rb")]
                _add_suffix_keys(
                    self.ruby_modules,
                    module_path,
                    file_id,
                    "/",
                )


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


def _lookup_longest_suffix(
    key: str,
    index: dict[str, int],
    separator: str,
    min_segments: int = 1,
) -> int | None:
    """Match the longest suffix of key that exists in index."""

    parts = [part for part in key.split(separator) if part]

    for start in range(len(parts)):
        if len(parts) - start < min_segments:
            break

        candidate = separator.join(parts[start:])
        resolved_id = index.get(candidate)

        if resolved_id is not None:
            return resolved_id

    return None


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


def _c_candidates(
    dependency_name: str,
    dependency_type: str,
    source_path: PurePosixPath,
) -> list[str]:
    """Build candidates for a C/C++ #include directive."""

    include_path = _normalize_path(dependency_name)

    if dependency_type == "local_include":
        relative = _normalize_path(
            str(source_path.parent / include_path)
        )

        candidates = [
            relative + extension
            for extension in C_EXTENSIONS
        ]

        candidates.append(include_path)

        return candidates

    return [include_path]


def _rust_candidates(
    dependency_name: str,
    source_path: PurePosixPath,
) -> tuple[list[str], list[str], str]:
    """
    Build candidate project paths for a Rust `use` declaration.

    Returns direct file candidates, module keys to try in the module index,
    and a base directory for `self`/`super` imports.
    """

    parts = [part for part in dependency_name.split("::") if part]

    if not parts:
        return [], [], ""

    head = parts[0]

    if head in RUST_EXTERNAL_PREFIXES:
        return [], [], ""

    base_path = None

    if head == "crate":
        parts = parts[1:]
    elif head == "self":
        parts = parts[1:]
        base_path = source_path.parent
    elif head == "super":
        base_path = source_path.parent
        index = 0

        while index < len(parts) and parts[index] == "super":
            base_path = base_path.parent
            index += 1

        parts = parts[index:]

    base = ""

    if base_path is not None and str(base_path) != ".":
        base = str(base_path)

    direct: list[str] = []
    module_keys: list[str] = []

    for length in range(len(parts), 0, -1):
        module_path = "/".join(parts[:length])
        module_keys.append(module_path)

        if base:
            target = posixpath.join(base, module_path)
            direct.append(target + ".rs")
            direct.append(target + "/mod.rs")
        else:
            direct.append(module_path + ".rs")
            direct.append(module_path + "/mod.rs")
            direct.append("src/" + module_path + ".rs")
            direct.append("src/" + module_path + "/mod.rs")

    return direct, module_keys, base


def _go_candidates(dependency_name: str) -> list[str]:
    """
    Build candidate package directories for a Go import.

    Go imports reference packages (directories). Standard-library imports
    such as "fmt" have no domain or slash and stay unresolved.
    """

    if "/" not in dependency_name and "." not in dependency_name:
        return []

    parts = dependency_name.split("/")

    return [
        "/".join(parts[start:])
        for start in range(len(parts))
    ]


def _php_candidates(dependency_name: str) -> str:
    """Convert a PHP namespace into a class-path key."""

    return dependency_name.replace("\\", "/").strip("/")


def _ruby_candidates(
    dependency_name: str,
    dependency_type: str,
    source_path: PurePosixPath,
) -> list[str]:
    """Build candidates for a Ruby require/require_relative."""

    name = _normalize_path(dependency_name)

    if name.endswith(".rb"):
        name = name[: -len(".rb")]

    if dependency_type == "require_relative":
        target = _normalize_path(str(source_path.parent / name))

        return [target + ".rb", target]

    return [name + ".rb", name]


def _clean_asset_reference(dependency_name: str) -> str:
    """Remove query strings and fragments from an asset reference."""

    reference = (dependency_name or "").strip()

    for separator in ("#", "?"):
        if separator in reference:
            reference = reference.split(separator, 1)[0]

    return reference


def _asset_candidates(
    dependency_name: str,
    source_path: PurePosixPath,
) -> list[str]:
    """
    Build candidate project paths for an HTML/CSS/template reference.

    References starting with "/" are project-root relative, everything
    else is relative to the referencing file, matching browser and
    template engine behaviour.
    """

    reference = _clean_asset_reference(dependency_name)

    if not reference:
        return []

    if reference.startswith("/"):
        base = _normalize_path(reference.lstrip("/"))
    else:
        base = _normalize_path(str(source_path.parent / reference))

    if not base:
        return []

    return [base]


def _resolve_markup(
    dependency_name: str,
    source_path: PurePosixPath,
    index: _ProjectIndex,
) -> int | None:
    """
    Resolve a stylesheet, script or template reference to a project file.
    """

    resolved_id = _first_match(
        _asset_candidates(dependency_name, source_path),
        index.files,
        index.files_lower,
    )

    if resolved_id is not None:
        return resolved_id

    # Static folders and template roots are often not the project root,
    # so fall back to the longest matching path suffix.
    reference = _clean_asset_reference(dependency_name)

    if reference.startswith("/"):
        reference = reference.lstrip("/")

    if not reference or reference.startswith(".."):
        return None

    normalized = _normalize_path(reference)

    return (
        index.path_suffixes.get(normalized)
        or index.files_lower.get(normalized.lower())
    )


def _resolve_python(
    dependency_name: str,
    source_path: PurePosixPath,
    index: _ProjectIndex,
) -> int | None:
    resolved_id = _first_match(
        _python_candidates(dependency_name, source_path),
        index.files,
        index.files_lower,
    )

    if resolved_id is not None:
        return resolved_id

    leading_dots = len(dependency_name) - len(
        dependency_name.lstrip(".")
    )

    if leading_dots:
        return None

    return index.python_modules.get(dependency_name)


def _resolve_javascript(
    dependency_name: str,
    source_path: PurePosixPath,
    index: _ProjectIndex,
) -> int | None:
    return _first_match(
        _javascript_candidates(dependency_name, source_path),
        index.files,
        index.files_lower,
    )


def _resolve_java(
    dependency_name: str,
    index: _ProjectIndex,
) -> int | None:
    if dependency_name.startswith(JAVA_EXTERNAL_PREFIXES):
        return None

    class_path = dependency_name.replace(".", "/").lower()

    if "*" in class_path:
        return None

    return _lookup_longest_suffix(
        class_path,
        index.java_classes,
        "/",
        min_segments=2,
    )


def _resolve_c(
    dependency_name: str,
    dependency_type: str,
    source_path: PurePosixPath,
    index: _ProjectIndex,
) -> int | None:
    candidates = _c_candidates(
        dependency_name,
        dependency_type,
        source_path,
    )

    resolved_id = _first_match(
        candidates,
        index.files,
        index.files_lower,
    )

    if resolved_id is not None:
        return resolved_id

    # Headers are often included from an include root that is not the
    # project root, so fall back to a path-suffix match.
    include_path = _normalize_path(dependency_name)

    if include_path.startswith(".."):
        return None

    return index.path_suffixes.get(include_path)


def _resolve_go(
    dependency_name: str,
    index: _ProjectIndex,
) -> int | None:
    for candidate in _go_candidates(dependency_name):
        resolved_id = index.directories.get(candidate)

        if resolved_id is not None:
            return resolved_id

    return None


def _resolve_rust(
    dependency_name: str,
    source_path: PurePosixPath,
    index: _ProjectIndex,
) -> int | None:
    candidates, module_keys, base = _rust_candidates(
        dependency_name,
        source_path,
    )

    resolved_id = _first_match(
        candidates,
        index.files,
        index.files_lower,
    )

    if resolved_id is not None:
        return resolved_id

    for module_key in module_keys:
        if base:
            continue

        resolved_id = index.rust_modules.get(module_key)

        if resolved_id is not None:
            return resolved_id

    return None


def _resolve_php(
    dependency_name: str,
    index: _ProjectIndex,
) -> int | None:
    return _lookup_longest_suffix(
        _php_candidates(dependency_name).lower(),
        index.php_classes,
        "/",
        min_segments=2,
    )


def _resolve_ruby(
    dependency_name: str,
    dependency_type: str,
    source_path: PurePosixPath,
    index: _ProjectIndex,
) -> int | None:
    candidates = _ruby_candidates(
        dependency_name,
        dependency_type,
        source_path,
    )

    resolved_id = _first_match(
        candidates,
        index.files,
        index.files_lower,
    )

    if resolved_id is not None:
        return resolved_id

    if dependency_type == "require_relative":
        return None

    name = _normalize_path(dependency_name)

    if name.endswith(".rb"):
        name = name[: -len(".rb")]

    return _lookup_longest_suffix(
        name,
        index.ruby_modules,
        "/",
    )


def resolve_dependencies(
    dependencies: list[Dependency],
    project_files: list[ProjectFile],
) -> int:
    """
    Resolve local dependencies to files within the same project.

    Supports Python, JavaScript/TypeScript, Java/Kotlin, C/C++, Go, Rust,
    PHP, and Ruby. External packages remain unresolved.
    """

    index = _ProjectIndex(project_files)

    resolved_count = 0

    for dependency in dependencies:

        # Reset any previous resolution.
        dependency.resolved_file_id = None

        source_file = index.by_id.get(dependency.file_id)

        if source_file is None:
            continue

        source_path = PurePosixPath(
            _normalize_path(source_file.relative_path)
        )

        language = (source_file.language or "").lower()
        dependency_name = dependency.dependency_name
        dependency_type = dependency.dependency_type or ""

        resolved_id = None

        if language == "python":
            resolved_id = _resolve_python(
                dependency_name,
                source_path,
                index,
            )

        elif language in JAVASCRIPT_LANGUAGES:
            # Bare package names (react, axios, ...) are external.
            if dependency_name.startswith((".", "/")):
                resolved_id = _resolve_javascript(
                    dependency_name,
                    source_path,
                    index,
                )

        elif language in JAVA_LANGUAGES:
            resolved_id = _resolve_java(dependency_name, index)

        elif language in C_LANGUAGES:
            resolved_id = _resolve_c(
                dependency_name,
                dependency_type,
                source_path,
                index,
            )

        elif language == "go":
            resolved_id = _resolve_go(dependency_name, index)

        elif language == "rust":
            resolved_id = _resolve_rust(
                dependency_name,
                source_path,
                index,
            )

        elif language == "php":
            resolved_id = _resolve_php(dependency_name, index)

        elif language == "ruby":
            resolved_id = _resolve_ruby(
                dependency_name,
                dependency_type,
                source_path,
                index,
            )

        elif language in MARKUP_LANGUAGES:
            # Stylesheets, scripts and template includes.
            if dependency_type in (
                "stylesheet",
                "script",
                "template_include",
                "template_extends",
            ):
                resolved_id = _resolve_markup(
                    dependency_name,
                    source_path,
                    index,
                )

        elif language in STYLESHEET_LANGUAGES:
            if dependency_type == "css_import":
                resolved_id = _resolve_markup(
                    dependency_name,
                    source_path,
                    index,
                )

        if resolved_id is not None:
            dependency.resolved_file_id = resolved_id
            resolved_count += 1

    return resolved_count
