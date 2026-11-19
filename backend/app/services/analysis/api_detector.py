import re

from pathlib import Path

from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.project_file import ProjectFile
from app.services.analysis.framework_detector import (
    detect_project_technologies,
)
from app.services.analysis.file_scanner import is_sensitive_file


# Only read reasonably sized source files while looking for routes.
MAX_SCAN_FILE_SIZE = 1024 * 1024
MAX_SCAN_FILES = 5000
MAX_ENDPOINTS = 1000

HTTP_METHODS = (
    "GET",
    "POST",
    "PUT",
    "PATCH",
    "DELETE",
    "HEAD",
    "OPTIONS",
)

# Files that only exercise endpoints rather than defining them.
IGNORED_PATH_PARTS = {
    "test",
    "tests",
    "__tests__",
    "spec",
    "specs",
    "fixtures",
    "__fixtures__",
    "benchmark",
    "benchmarks",
    "migrations",
    "node_modules",
    "vendor",
}

IGNORED_FILENAME_PARTS = (
    ".test.",
    ".spec.",
    "_test.",
    "_tests.",
)

PYTHON_DECORATOR_PATTERN = re.compile(
    r"^[ \t]*@(?P<owner>[A-Za-z_][\w.]*)\."
    r"(?P<method>get|post|put|patch|delete|head|options|route|websocket)"
    r"\s*\((?P<arguments>[^\n]*)$",
    re.IGNORECASE | re.MULTILINE,
)

PYTHON_PATH_PATTERN = re.compile(r"""["'](?P<path>/[^"']*)["']""")

PYTHON_METHODS_PATTERN = re.compile(
    r"methods\s*=\s*\[(?P<methods>[^\]]*)\]",
    re.IGNORECASE | re.DOTALL,
)

PYTHON_STRING_PATTERN = re.compile(r"""["']([A-Za-z]+)["']""")

DJANGO_URL_PATTERN = re.compile(
    r"^[ \t]*(?:path|re_path|url)\s*\(\s*"
    r"""(?:r?["'](?P<path>[^"']*)["'])""",
    re.MULTILINE,
)

JAVASCRIPT_ROUTE_PATTERN = re.compile(
    r"\b(?:app|router|server|api)\."
    r"(?P<method>get|post|put|patch|delete|head|options|all)"
    r"\s*\(\s*[`'\"](?P<path>/[^`'\"]*)[`'\"]",
    re.IGNORECASE,
)

JAVASCRIPT_EXPORT_PATTERN = re.compile(
    r"export\s+(?:async\s+)?(?:function|const|let)\s+"
    r"(?P<method>GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\b"
)

JAVA_MAPPING_PATTERN = re.compile(
    r"@(?P<mapping>Get|Post|Put|Patch|Delete|Request)Mapping"
    r"\s*\((?P<arguments>[^)]*)\)",
    re.IGNORECASE | re.DOTALL,
)

JAVA_PATH_PATTERN = re.compile(
    r"""(?:value\s*=\s*)?["'](?P<path>/[^"']*)["']"""
)

JAVA_REQUEST_METHODS_PATTERN = re.compile(
    r"RequestMethod\.(?P<method>GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)",
    re.IGNORECASE,
)

GO_ROUTE_PATTERN = re.compile(
    r"\.[ \t]*(?P<method>GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS|"
    r"Get|Post|Put|Patch|Delete|Head|Options|Any)"
    r"\s*\(\s*\"(?P<path>/[^\"]*)\""
)

PHP_ROUTE_PATTERN = re.compile(
    r"Route::(?P<method>get|post|put|patch|delete|any|resource)"
    r"\s*\(\s*['\"](?P<path>/[^'\"]*)['\"]",
    re.IGNORECASE,
)

RUBY_ROUTE_PATTERN = re.compile(
    r"^[ \t]*(?P<method>get|post|put|patch|delete)"
    r"[ \t]+['\"](?P<path>/[^'\"]*)['\"]",
    re.MULTILINE,
)

CSHARP_ROUTE_PATTERN = re.compile(
    r"\[Http(?P<method>Get|Post|Put|Patch|Delete|Head|Options)"
    r"(?:\s*\(\s*\"(?P<path>[^\"]*)\"\s*\))?\]",
    re.IGNORECASE,
)

RUST_ATTRIBUTE_PATTERN = re.compile(
    r"#\[(?P<method>get|post|put|patch|delete|head|options)"
    r"\s*\(\s*\"(?P<path>/[^\"]*)\"\s*\)\]",
    re.IGNORECASE,
)

SWIFT_ROUTE_PATTERN = re.compile(
    r"\b(?:app|routes)\."
    r"(?P<method>get|post|put|patch|delete|head|options)"
    r"\s*\(\s*\"(?P<path>/[^\"]*)\"",
    re.IGNORECASE,
)

ELIXIR_ROUTE_PATTERN = re.compile(
    r"^[ \t]*(?P<method>get|post|put|patch|delete)"
    r"[ \t]+\"(?P<path>/[^\"]*)\"",
    re.MULTILINE,
)

# File-based API routes (Next.js App Router and Pages Router).
NEXT_APP_ROUTE_PATTERN = re.compile(r"(?:^|/)app/api/(?P<path>.+)/route\.[jt]sx?$")
NEXT_PAGES_ROUTE_PATTERN = re.compile(r"(?:^|/)pages/api/(?P<path>.+)\.[jt]sx?$")


def _normalize_method(method: str) -> str:
    upper = method.upper()

    if upper == "ALL" or upper == "ANY":
        return "ANY"

    return upper


def _line_number(source_code: str, offset: int) -> int:
    return source_code.count("\n", 0, offset) + 1


def _should_scan(project_file: ProjectFile) -> bool:
    relative_path = (project_file.relative_path or "").replace("\\", "/")
    parts = {part.lower() for part in relative_path.split("/")[:-1]}
    filename = (project_file.filename or "").lower()

    if parts & IGNORED_PATH_PARTS:
        return False

    if any(part in filename for part in IGNORED_FILENAME_PARTS):
        return False

    return not is_sensitive_file(filename)


def _read_source(root: Path, project_file: ProjectFile) -> str | None:
    try:
        candidate = root / project_file.relative_path

        if candidate.is_symlink():
            return None

        file_path = candidate.resolve(strict=True)

        if not file_path.is_relative_to(root) or not file_path.is_file():
            return None

        if file_path.stat().st_size > MAX_SCAN_FILE_SIZE:
            return None

        return file_path.read_text(encoding="utf-8", errors="replace")

    except (OSError, ValueError):
        return None


def _python_framework(languages: set[str], frameworks: set[str]) -> str:
    if "FastAPI" in frameworks and "Flask" not in frameworks:
        return "FastAPI"

    if "Flask" in frameworks and "FastAPI" not in frameworks:
        return "Flask"

    if "FastAPI" in frameworks:
        return "FastAPI"

    if "Flask" in frameworks:
        return "Flask"

    return "Python"


def _javascript_framework(frameworks: set[str]) -> str:
    if "Next.js" in frameworks:
        return "Next.js"

    if "NestJS" in frameworks:
        return "NestJS"

    if "Express.js" in frameworks:
        return "Express.js"

    return "JavaScript"


def _detect_python_routes(
    source_code: str,
    framework: str,
) -> list[dict]:
    endpoints = []

    for match in PYTHON_DECORATOR_PATTERN.finditer(source_code):
        method = match.group("method").lower()
        arguments = match.group("arguments")

        # A decorator may continue on the next lines.
        if ")" not in arguments:
            tail = source_code[match.end():match.end() + 400]
            closing = tail.find(")")

            if closing != -1:
                arguments += tail[: closing + 1]

        path_match = PYTHON_PATH_PATTERN.search(arguments)

        if not path_match:
            continue

        path = path_match.group("path")

        if method == "websocket":
            endpoints.append({
                "method": "WS",
                "path": path,
                "framework": framework,
                "line": _line_number(source_code, match.start()),
            })
            continue

        if method == "route":
            methods_match = PYTHON_METHODS_PATTERN.search(arguments)
            methods = (
                [
                    _normalize_method(name)
                    for name in PYTHON_STRING_PATTERN.findall(
                        methods_match.group("methods")
                    )
                    if name.upper() in HTTP_METHODS
                ]
                if methods_match
                else ["GET"]
            )
        else:
            methods = [_normalize_method(method)]

        for detected_method in methods:
            endpoints.append({
                "method": detected_method,
                "path": path,
                "framework": framework,
                "line": _line_number(source_code, match.start()),
            })

    return endpoints


def _detect_django_routes(source_code: str, file_path: str) -> list[dict]:
    if not file_path.endswith("urls.py"):
        return []

    endpoints = []

    for match in DJANGO_URL_PATTERN.finditer(source_code):
        path = match.group("path")

        endpoints.append({
            "method": "ROUTE",
            "path": "/" + path.lstrip("^/") if path else "/",
            "framework": "Django",
            "line": _line_number(source_code, match.start()),
        })

    return endpoints


def _detect_javascript_routes(
    source_code: str,
    framework: str,
    relative_path: str,
) -> list[dict]:
    endpoints = []

    # Express-style route registration. The registering object decides the
    # label; a repository-level Next.js dependency does not make every
    # `app.get` call a Next.js route.
    for match in JAVASCRIPT_ROUTE_PATTERN.finditer(source_code):
        endpoints.append({
            "method": _normalize_method(match.group("method")),
            "path": match.group("path"),
            "framework": (
                "Express.js" if framework != "NestJS" else "NestJS"
            ),
            "line": _line_number(source_code, match.start()),
        })

    # Next.js file-based routes.
    next_match = (
        NEXT_APP_ROUTE_PATTERN.search(relative_path)
        or NEXT_PAGES_ROUTE_PATTERN.search(relative_path)
    )

    if next_match:
        route_path = "/api/" + next_match.group("path").strip("/")
        route_path = re.sub(r"/index$", "", route_path)
        route_path = re.sub(r"\[([^\]]+)\]", r":\1", route_path)

        exported_methods = [
            _normalize_method(method)
            for method in JAVASCRIPT_EXPORT_PATTERN.findall(source_code)
        ] or ["ANY"]

        for method in dict.fromkeys(exported_methods):
            endpoints.append({
                "method": method,
                "path": route_path,
                "framework": "Next.js",
                "line": 1,
            })

    return endpoints


def _detect_java_routes(source_code: str, framework: str) -> list[dict]:
    endpoints = []

    for match in JAVA_MAPPING_PATTERN.finditer(source_code):
        mapping = match.group("mapping").lower()
        arguments = match.group("arguments")
        path_match = JAVA_PATH_PATTERN.search(arguments)
        path = path_match.group("path") if path_match else "/"

        if mapping == "request":
            methods = [
                _normalize_method(method)
                for method in JAVA_REQUEST_METHODS_PATTERN.findall(arguments)
            ] or ["ANY"]
        else:
            methods = [_normalize_method(mapping)]

        for method in methods:
            endpoints.append({
                "method": method,
                "path": path,
                "framework": framework,
                "line": _line_number(source_code, match.start()),
            })

    return endpoints


def _detect_simple_pattern(
    source_code: str,
    pattern: re.Pattern,
    framework: str,
    default_path: str | None = None,
) -> list[dict]:
    endpoints = []

    for match in pattern.finditer(source_code):
        groups = match.groupdict()
        path = groups.get("path") or default_path

        if path is None:
            continue

        if path and not path.startswith("/"):
            path = "/" + path

        endpoints.append({
            "method": _normalize_method(groups["method"]),
            "path": path or "/",
            "framework": framework,
            "line": _line_number(source_code, match.start()),
        })

    return endpoints


def _scan_file(
    source_code: str,
    project_file: ProjectFile,
    languages: set[str],
    frameworks: set[str],
) -> list[dict]:
    language = (project_file.language or "").lower()
    relative_path = (project_file.relative_path or "").replace("\\", "/")

    if language == "python":
        framework = _python_framework(languages, frameworks)
        return (
            _detect_django_routes(source_code, relative_path)
            if relative_path.endswith("urls.py")
            else _detect_python_routes(source_code, framework)
        )

    if language in {"javascript", "typescript", "tsx"}:
        return _detect_javascript_routes(
            source_code,
            _javascript_framework(frameworks),
            relative_path,
        )

    if language in {"java", "kotlin", "scala"}:
        framework = (
            "Spring Boot"
            if "Spring Boot" in frameworks
            else "Spring Framework"
            if "Spring Framework" in frameworks
            else "JVM"
        )
        return _detect_java_routes(source_code, framework)

    if language == "go":
        framework = (
            "Gin"
            if "Gin" in frameworks
            else "Echo"
            if "Echo" in frameworks
            else "Fiber"
            if "Fiber" in frameworks
            else "Chi"
            if "Chi" in frameworks
            else "Go"
        )
        return _detect_simple_pattern(
            source_code, GO_ROUTE_PATTERN, framework
        )

    if language == "php":
        framework = "Laravel" if "Laravel" in frameworks else "PHP"
        return _detect_simple_pattern(
            source_code, PHP_ROUTE_PATTERN, framework
        )

    if language == "ruby":
        framework = (
            "Ruby on Rails"
            if "Ruby on Rails" in frameworks
            else "Ruby"
        )
        return _detect_simple_pattern(
            source_code, RUBY_ROUTE_PATTERN, framework
        )

    if language == "c#":
        framework = "ASP.NET"
        return _detect_simple_pattern(
            source_code,
            CSHARP_ROUTE_PATTERN,
            framework,
            default_path="/",
        )

    if language == "rust":
        framework = (
            "Actix Web"
            if "Actix Web" in frameworks
            else "Axum"
            if "Axum" in frameworks
            else "Rocket"
            if "Rocket" in frameworks
            else "Rust"
        )
        return _detect_simple_pattern(
            source_code, RUST_ATTRIBUTE_PATTERN, framework
        )

    if language == "swift":
        framework = "Vapor" if "Vapor" in frameworks else "Swift"
        return _detect_simple_pattern(
            source_code, SWIFT_ROUTE_PATTERN, framework
        )

    if language == "elixir":
        return _detect_simple_pattern(
            source_code, ELIXIR_ROUTE_PATTERN, "Phoenix"
        )

    return []


def detect_project_api_endpoints(
    db: Session,
    project_id: int,
) -> dict:
    """
    Detect HTTP API endpoints defined in a project's source code.

    Detection reads source text only; imported code is never executed.
    Results are derived from decorators, route registrations and
    file-based routes for the supported frameworks.
    """

    project = db.query(Project).filter(
        Project.id == project_id
    ).first()

    if not project:
        raise ValueError("Project not found.")

    project_files = (
        db.query(ProjectFile)
        .filter(ProjectFile.project_id == project_id)
        .order_by(ProjectFile.relative_path.asc())
        .all()
    )

    if not project.root_path:
        return {
            "total": 0,
            "frameworks": [],
            "endpoints": [],
            "scanned_files": 0,
        }

    try:
        root = Path(project.root_path).resolve(strict=True)
    except (OSError, ValueError):
        return {
            "total": 0,
            "frameworks": [],
            "endpoints": [],
            "scanned_files": 0,
        }

    if not root.is_dir():
        return {
            "total": 0,
            "frameworks": [],
            "endpoints": [],
            "scanned_files": 0,
        }

    technologies = detect_project_technologies(db, project_id)
    languages = {
        language.lower()
        for language in technologies.get("languages", [])
    }
    frameworks = set(technologies.get("frameworks", []))

    endpoints = []
    scanned_files = 0

    for project_file in project_files:
        if scanned_files >= MAX_SCAN_FILES:
            break

        if not _should_scan(project_file):
            continue

        source_code = _read_source(root, project_file)

        if source_code is None:
            continue

        scanned_files += 1

        for endpoint in _scan_file(
            source_code,
            project_file,
            languages,
            frameworks,
        ):
            endpoints.append({
                **endpoint,
                "file": project_file.relative_path,
            })

        if len(endpoints) >= MAX_ENDPOINTS:
            break

    # Remove duplicates caused by nested decorators or repeated routes.
    unique_endpoints = []
    seen = set()

    for endpoint in endpoints:
        key = (
            endpoint["method"],
            endpoint["path"],
            endpoint["file"],
            endpoint["line"],
        )

        if key in seen:
            continue

        seen.add(key)
        unique_endpoints.append(endpoint)

    unique_endpoints.sort(
        key=lambda item: (
            item["path"],
            item["method"],
            item["file"],
            item["line"],
        )
    )

    detected_frameworks = sorted({
        endpoint["framework"]
        for endpoint in unique_endpoints
    })

    return {
        "total": len(unique_endpoints),
        "frameworks": detected_frameworks,
        "endpoints": unique_endpoints,
        "scanned_files": scanned_files,
    }
