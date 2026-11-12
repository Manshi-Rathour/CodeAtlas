
import os
from pathlib import Path
from collections import Counter


# Directories that should not be scanned
IGNORED_DIRECTORIES = {
    ".git",
    ".svn",
    ".hg",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".venv",
    "venv",
    "env",
    "virtualenv",
    "node_modules",
    "bower_components",
    "vendor",
    "dist",
    "build",
    "target",
    "out",
    ".next",
    ".nuxt",
    ".turbo",
    ".idea",
    ".vscode",
    "coverage",
    ".coverage",
    "site-packages",
    "Pods",
    "DerivedData",
}


# Files and extensions that may contain sensitive information
SENSITIVE_FILENAMES = {
    ".env",
    ".env.local",
    ".env.production",
    ".env.development",
    "id_rsa",
    "id_ed25519",
    "credentials",
    "secrets.json",
    "service-account.json",
}

SENSITIVE_EXTENSIONS = {
    ".pem",
    ".key",
    ".p12",
    ".pfx",
    ".keystore",
    ".jks",
}


# Maximum file size considered for inventory
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2 MB


# File extension to programming language mapping
LANGUAGE_MAP = {
    ".py": "Python",
    ".pyw": "Python",

    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".mjs": "JavaScript",
    ".cjs": "JavaScript",

    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".mts": "TypeScript",
    ".cts": "TypeScript",

    ".java": "Java",
    ".kt": "Kotlin",
    ".kts": "Kotlin",
    ".scala": "Scala",

    ".c": "C",
    ".h": "C",
    ".cpp": "C++",
    ".cc": "C++",
    ".cxx": "C++",
    ".hpp": "C++",
    ".hh": "C++",

    ".cs": "C#",
    ".fs": "F#",

    ".go": "Go",
    ".rs": "Rust",

    ".php": "PHP",
    ".rb": "Ruby",
    ".swift": "Swift",

    ".html": "HTML",
    ".htm": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".sass": "Sass",
    ".less": "Less",

    ".vue": "Vue",
    ".svelte": "Svelte",

    ".sql": "SQL",
    ".sh": "Shell",
    ".bash": "Shell",
    ".zsh": "Shell",
    ".ps1": "PowerShell",
    ".bat": "Batch",
    ".cmd": "Batch",

    ".r": "R",
    ".R": "R",
    ".jl": "Julia",
    ".lua": "Lua",
    ".pl": "Perl",
    ".pm": "Perl",

    ".dart": "Dart",
    ".ex": "Elixir",
    ".exs": "Elixir",
    ".erl": "Erlang",
    ".hrl": "Erlang",

    ".hs": "Haskell",
    ".lhs": "Haskell",
    ".ml": "OCaml",
    ".mli": "OCaml",

    ".clj": "Clojure",
    ".cljs": "ClojureScript",
    ".cljc": "Clojure",

    ".scala": "Scala",
    ".groovy": "Groovy",
    ".gradle": "Gradle",

    ".tf": "Terraform",
    ".hcl": "HCL",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".toml": "TOML",
    ".xml": "XML",
    ".json": "JSON",

    ".md": "Markdown",
    ".mdx": "MDX",
    ".rst": "reStructuredText",

    ".ipynb": "Jupyter Notebook",
    ".proto": "Protocol Buffers",
    ".graphql": "GraphQL",
    ".gql": "GraphQL",

    ".dockerfile": "Dockerfile",
    ".makefile": "Makefile",
}


# Special filenames without normal extensions
SPECIAL_FILENAME_MAP = {
    "dockerfile": "Dockerfile",
    "makefile": "Makefile",
    "gnumakefile": "Makefile",
    "jenkinsfile": "Groovy",
    "vagrantfile": "Ruby",
    "procfile": "Procfile",
}


def detect_language(filename: str) -> str:
    """
    Detect the programming language or file type
    using the filename and its extension.
    """
    lower_name = filename.lower()

    if lower_name in SPECIAL_FILENAME_MAP:
        return SPECIAL_FILENAME_MAP[lower_name]

    extension = Path(filename).suffix.lower()

    return LANGUAGE_MAP.get(extension, "Other")


def is_sensitive_file(filename: str) -> bool:
    """
    Check whether a filename or extension indicates
    that the file may contain sensitive information.
    """

    lower_name = filename.lower()
    extension = Path(filename).suffix.lower()

    if lower_name in SENSITIVE_FILENAMES:
        return True

    if lower_name.startswith(".env"):
        return True

    if extension in SENSITIVE_EXTENSIONS:
        return True

    if "secret" in lower_name or "credential" in lower_name:
        return True

    return False


def is_binary_file(file_path: Path) -> bool:
    """
    Detect binary files without executing or loading
    the complete file into memory.
    """

    try:
        with file_path.open("rb") as file:
            sample = file.read(8192)

        if b"\x00" in sample:
            return True

        try:
            sample.decode("utf-8")
        except UnicodeDecodeError:
            return True

        return False

    except (OSError, PermissionError):
        return True


def scan_project(root_path: str | Path) -> dict:
    """
    Recursively scan a project and generate a
    universal file inventory.

    The scanner does not execute uploaded code.
    """

    root = Path(root_path).resolve()

    if not root.exists():
        raise ValueError("Project directory does not exist.")

    if not root.is_dir():
        raise ValueError("Provided project path is not a directory.")

    files = []

    skipped = {
        "sensitive": 0,
        "binary": 0,
        "oversized": 0,
        "symlink": 0,
        "unreadable": 0,
        "invalid_extension": 0
    }

    language_counts = Counter()

    for current_root, directories, filenames in os.walk(
        root,
        topdown=True,
        followlinks=False
    ):

        current_path = Path(current_root)

        # Skip ignored directories and directory symlinks
        filtered_directories = []

        for directory in directories:

            directory_path = current_path / directory

            if directory in IGNORED_DIRECTORIES:
                continue

            if directory_path.is_symlink():
                skipped["symlink"] += 1
                continue

            filtered_directories.append(directory)

        directories[:] = filtered_directories

        for filename in filenames:

            file_path = current_path / filename

            try:
                # Never follow symbolic links
                if file_path.is_symlink():
                    skipped["symlink"] += 1
                    continue

                # Ignore sensitive files
                if is_sensitive_file(filename):
                    skipped["sensitive"] += 1
                    continue

                # Resolve and verify that the file is
                # still inside the project directory
                resolved_path = file_path.resolve()

                if not resolved_path.is_relative_to(root):
                    skipped["symlink"] += 1
                    continue

                # Only consider regular files
                if not resolved_path.is_file():
                    continue

                file_size = resolved_path.stat().st_size

                # Ignore oversized files
                if file_size > MAX_FILE_SIZE:
                    skipped["oversized"] += 1
                    continue

                # Ignore files with extensions longer than the database limit
                extension = resolved_path.suffix.lower()

                if len(extension) > 30:
                    skipped["invalid_extension"] += 1
                    continue

                # Ignore binary files
                if is_binary_file(resolved_path):
                    skipped["binary"] += 1
                    continue

                relative_path = resolved_path.relative_to(root)

                language = detect_language(filename)

                file_record = {
                    "filename": filename,
                    "relative_path": relative_path.as_posix(),
                    "extension": extension,
                    "language": language,
                    "size_bytes": file_size,
                }

                files.append(file_record)

                language_counts[language] += 1

            except (OSError, PermissionError, ValueError):
                skipped["unreadable"] += 1
                continue

    return {
        "root_path": str(root),
        "total_files": len(files),
        "files": files,
        "language_counts": dict(language_counts),
        "skipped": skipped,
    }
