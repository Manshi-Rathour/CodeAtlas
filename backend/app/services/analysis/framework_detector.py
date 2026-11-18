import json
import re
import tomllib
import xml.etree.ElementTree as ET

from pathlib import Path

from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.project_file import ProjectFile
from app.models.dependency import Dependency


LANGUAGE_NAMES = {
    "python": "Python",
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "tsx": "TSX",
    "java": "Java",
    "c++": "C++",
    "c": "C",
    "go": "Go",
    "rust": "Rust",
    "php": "PHP",
    "ruby": "Ruby",
    "html": "HTML",
    "css": "CSS",
    "sql": "SQL",
    "swift": "Swift",
    "kotlin": "Kotlin",
}


FRAMEWORK_RULES = {
    "Django": ["django"],
    "Flask": ["flask"],
    "FastAPI": ["fastapi"],

    "React": ["react"],
    "Next.js": ["next"],
    "Express.js": ["express"],
    "Vue.js": ["vue"],
    "Angular": ["@angular/core"],
    "Svelte": ["svelte"],
    "NestJS": ["@nestjs/core"],

    "Spring Boot": ["org.springframework.boot"],
    "Spring Framework": [
        "org.springframework.core",
        "org.springframework.context",
        "org.springframework.beans",
        "org.springframework.web",
        "org.springframework.aop",
        "org.springframework.jdbc",
        "org.springframework.orm",
        "org.springframework.transaction",
],
    "Ktor": ["io.ktor"],

    "Gin": ["github.com/gin-gonic/gin"],
    "Echo": ["github.com/labstack/echo"],
    "Fiber": ["github.com/gofiber/fiber"],
    "Chi": ["github.com/go-chi/chi"],

    "Actix Web": ["actix_web"],
    "Axum": ["axum"],
    "Rocket": ["rocket"],

    "Laravel": ["illuminate", "laravel"],
    "Symfony": ["symfony", "symfony.component"],

    "Ruby on Rails": ["rails"],
    "Sinatra": ["sinatra"],

    "Vapor": ["vapor"],

    "Qt": ["qt", "qtcore", "qtwidgets"],
    "GTK": ["gtk", "gtk.h"],
}


LIBRARY_RULES = {
    "SQLAlchemy": ["sqlalchemy"],
    "NumPy": ["numpy"],
    "Pandas": ["pandas"],
    "TensorFlow": ["tensorflow"],
    "PyTorch": ["torch"],
    "OpenCV": ["cv2", "opencv"],

    "Axios": ["axios"],
    "Lodash": ["lodash"],
    "jQuery": ["jquery"],

    "Boost": ["boost"],
    "GLib": ["glib"],

    "Serde": ["serde"],
    "Tokio": ["tokio"],

    "GORM": ["gorm.io/gorm"],
}


DATABASE_RULES = {
    "PostgreSQL": [
        "psycopg",
        "psycopg2",
        "asyncpg",
        "pg",
        "pgx",
        "lib/pq",
        "postgres",
        "postgresql",
    ],
    "MySQL": [
        "mysql",
        "mysql2",
        "pymysql",
        "mysqlclient",
        "mysql.connector",
    ],
    "SQLite": [
        "sqlite3",
        "rusqlite",
        "sqlite",
    ],
    "MongoDB": [
        "pymongo",
        "mongoose",
        "mongodb",
    ],
    "Redis": [
        "redis",
        "ioredis",
        "go-redis",
    ],
}


MAX_MANIFEST_SIZE = 1024 * 1024

MANIFEST_FILES = {
    "package.json",
    "requirements.txt",
    "pyproject.toml",
    "pipfile",
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
    "go.mod",
    "cargo.toml",
    "composer.json",
    "gemfile",
    "package.swift",
}


def normalize_dependency(name: str) -> str:
    """
    Normalize dependency names for comparison.

    Package ecosystems use different separators for the same concept,
    for example Cargo's "actix-web" crate and the "actix_web" module.
    """
    return (
        name.strip()
        .lower()
        .replace("\\", ".")
        .replace("-", "_")
    )


def matches_dependency(
    dependency_name: str,
    patterns: list[str],
) -> bool:
    """
    Match exact dependency names, submodules and nested package paths.

    Examples:
    - "fastapi" matches the FastAPI rule.
    - "fastapi.middleware" matches FastAPI.
    - "github.com/lib/pq" matches the nested "lib/pq" rule.
    - "psycopg2-binary" matches the "psycopg2" rule.
    """

    dependency = normalize_dependency(dependency_name)

    for pattern in patterns:
        normalized_pattern = normalize_dependency(pattern)

        if dependency == normalized_pattern:
            return True

        for separator in (".", "/", "::", "_"):
            if dependency.startswith(normalized_pattern + separator):
                return True

        # Nested package paths such as "github.com/lib/pq".
        if "/" in normalized_pattern:
            if dependency.endswith("/" + normalized_pattern):
                return True

    return False


def _add_dependency_names(
    names: set[str],
    values,
):
    """
    Add dependency names from a dictionary or list.
    """
    if isinstance(values, dict):
        names.update(
            str(name)
            for name in values
            if name
        )

    elif isinstance(values, list):
        for value in values:
            if not isinstance(value, str):
                continue

            match = re.match(
                r"^\s*([A-Za-z0-9_.-]+)",
                value
            )

            if match:
                names.add(match.group(1))


def _extract_manifest_dependencies(
    manifest_path: Path,
) -> set[str]:
    """
    Read dependencies from supported manifest files.

    Manifest files are treated as untrusted data.
    They are never executed.
    """
    names = set()
    filename = manifest_path.name.lower()

    try:
        if manifest_path.stat().st_size > MAX_MANIFEST_SIZE:
            return names

        content = manifest_path.read_text(
            encoding="utf-8",
            errors="replace"
        )

        if filename == "package.json":
            data = json.loads(content)

            for section in (
                "dependencies",
                "devDependencies",
                "peerDependencies",
                "optionalDependencies",
            ):
                _add_dependency_names(
                    names,
                    data.get(section, {})
                )

        elif filename == "requirements.txt":
            for line in content.splitlines():
                line = line.split("#", 1)[0].strip()

                match = re.match(
                    r"^([A-Za-z0-9_.-]+)",
                    line
                )

                if match:
                    names.add(match.group(1))

        elif filename == "pyproject.toml":
            data = tomllib.loads(content)

            project = data.get("project", {})

            _add_dependency_names(
                names,
                project.get("dependencies", [])
            )

            for values in project.get(
                "optional-dependencies", {}
            ).values():
                _add_dependency_names(names, values)

            poetry = data.get("tool", {}).get("poetry", {})

            _add_dependency_names(
                names,
                poetry.get("dependencies", {})
            )

            _add_dependency_names(
                names,
                poetry.get("dev-dependencies", {})
            )

        elif filename == "pipfile":
            data = tomllib.loads(content)

            _add_dependency_names(
                names,
                data.get("packages", {})
            )

            _add_dependency_names(
                names,
                data.get("dev-packages", {})
            )

        elif filename == "pom.xml":
            root = ET.fromstring(content)

            for element in root.iter():
                tag = element.tag.split("}")[-1]

                if tag in {"groupId", "artifactId"}:
                    if element.text:
                        names.add(element.text.strip())

        elif filename in {
            "build.gradle",
            "build.gradle.kts",
        }:
            matches = re.findall(
                r"""['"]([A-Za-z0-9_.-]+:[A-Za-z0-9_.-]+)(?::[^'"]*)?['"]""",
                content
            )

            names.update(matches)

        elif filename == "go.mod":
            for line in content.splitlines():
                line = line.strip()

                if line.startswith("//"):
                    continue

                match = re.match(
                    r"^(?:require\s+)?([A-Za-z0-9_.@/-]+)\s+v",
                    line
                )

                if match:
                    names.add(match.group(1))

        elif filename == "cargo.toml":
            data = tomllib.loads(content)

            for section in (
                "dependencies",
                "dev-dependencies",
                "build-dependencies",
            ):
                _add_dependency_names(
                    names,
                    data.get(section, {})
                )

        elif filename == "composer.json":
            data = json.loads(content)

            for section in (
                "require",
                "require-dev",
            ):
                _add_dependency_names(
                    names,
                    data.get(section, {})
                )

        elif filename == "gemfile":
            matches = re.findall(
                r"""gem\s+['"]([^'"]+)['"]""",
                content
            )

            names.update(matches)

        elif filename == "package.swift":
            matches = re.findall(
                r"""package\s*\(\s*url:\s*['"]([^'"]+)['"]""",
                content
            )

            for url in matches:
                package_name = url.rstrip("/").split("/")[-1]
                package_name = package_name.removesuffix(".git")
                names.add(package_name)

    except (
        OSError,
        ValueError,
        TypeError,
        KeyError,
        ET.ParseError,
    ):
        # Ignore malformed or unreadable manifest files.
        return names

    return names


def detect_project_technologies(
    db: Session,
    project_id: int,
) -> dict:
    """
    Detect languages, frameworks, libraries and databases
    using stored imports and dependency manifests.
    """

    project = (
        db.query(Project)
        .filter(Project.id == project_id)
        .first()
    )

    if not project:
        raise ValueError("Project not found.")

    project_files = (
        db.query(ProjectFile)
        .filter(ProjectFile.project_id == project_id)
        .all()
    )

    dependencies = (
        db.query(Dependency)
        .filter(Dependency.project_id == project_id)
        .all()
    )

    # Identify programming languages.
    detected_languages = set()

    for project_file in project_files:
        language = (project_file.language or "").lower()

        if language in LANGUAGE_NAMES:
            detected_languages.add(
                LANGUAGE_NAMES[language]
            )

    # Collect dependencies extracted from source code.
    dependency_names = {
        dependency.dependency_name
        for dependency in dependencies
        if dependency.dependency_name
    }

    # Read dependency manifests from the project directory.
    if project.root_path:
        try:
            root_path = Path(project.root_path).resolve(
                strict=True
            )

            if root_path.is_dir():
                for project_file in project_files:
                    relative_path = Path(
                        project_file.relative_path
                    )

                    if relative_path.is_absolute():
                        continue

                    if relative_path.name.lower() not in MANIFEST_FILES:
                        continue

                    try:
                        manifest_path = (
                            root_path / relative_path
                        ).resolve(strict=True)

                        # Prevent path traversal and external symlinks.
                        manifest_path.relative_to(root_path)

                        if not manifest_path.is_file():
                            continue

                        manifest_dependencies = (
                            _extract_manifest_dependencies(
                                manifest_path
                            )
                        )

                        dependency_names.update(
                            manifest_dependencies
                        )

                    except (OSError, ValueError):
                        continue

        except (OSError, ValueError):
            pass

    frameworks = set()
    libraries = set()
    databases = set()

    # Detect frameworks.
    for framework, patterns in FRAMEWORK_RULES.items():
        if any(
            matches_dependency(name, patterns)
            for name in dependency_names
        ):
            frameworks.add(framework)

    # Detect libraries.
    for library, patterns in LIBRARY_RULES.items():
        if any(
            matches_dependency(name, patterns)
            for name in dependency_names
        ):
            libraries.add(library)

    # Detect databases.
    for database, patterns in DATABASE_RULES.items():
        if any(
            matches_dependency(name, patterns)
            for name in dependency_names
        ):
            databases.add(database)

    return {
        "languages": sorted(detected_languages),
        "frameworks": sorted(frameworks),
        "libraries": sorted(libraries),
        "databases": sorted(databases),
    }
