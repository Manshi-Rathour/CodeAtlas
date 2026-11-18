from app.models.dependency import Dependency
from app.models.project import Project
from app.models.project_file import ProjectFile
from app.services.analysis.analysis_service import analyze_project
from app.services.analysis.dependency_resolver import resolve_dependencies


class FakeFile:
    """Minimal ProjectFile stand-in for resolver unit tests."""

    def __init__(self, file_id, relative_path, language):
        self.id = file_id
        self.relative_path = relative_path
        self.language = language


class FakeDependency:
    """Minimal Dependency stand-in for resolver unit tests."""

    def __init__(self, file_id, dependency_name, dependency_type="import"):
        self.file_id = file_id
        self.dependency_name = dependency_name
        self.dependency_type = dependency_type
        self.resolved_file_id = None


def resolve_one(
    source_path,
    dependency_name,
    project_paths,
    language,
    dependency_type="import",
):
    source_id = 100
    files = [
        FakeFile(source_id, source_path, language)
    ]

    for index, path in enumerate(project_paths, start=1):
        files.append(
            FakeFile(index, path, language)
        )

    dependency = FakeDependency(
        source_id,
        dependency_name,
        dependency_type,
    )

    resolve_dependencies([dependency], files)

    return dependency.resolved_file_id


def test_resolves_relative_javascript_import():
    resolved = resolve_one(
        "src/main.jsx",
        "./App",
        ["src/App.jsx"],
        "JavaScript",
    )

    assert resolved == 1


def test_resolves_parent_directory_javascript_import():
    resolved = resolve_one(
        "src/components/Button.jsx",
        "../utils/format",
        ["src/utils/format.js"],
        "JavaScript",
    )

    assert resolved == 1


def test_resolves_javascript_index_file():
    resolved = resolve_one(
        "src/main.jsx",
        "./components",
        ["src/components/index.js"],
        "JavaScript",
    )

    assert resolved == 1


def test_resolves_javascript_import_with_extension():
    resolved = resolve_one(
        "src/main.tsx",
        "./App.tsx",
        ["src/App.tsx"],
        "TypeScript",
    )

    assert resolved == 1


def test_leaves_external_javascript_packages_unresolved():
    resolved = resolve_one(
        "src/main.jsx",
        "react",
        ["src/App.jsx"],
        "JavaScript",
    )

    assert resolved is None


def test_leaves_missing_local_javascript_import_unresolved():
    resolved = resolve_one(
        "src/main.jsx",
        "./Missing",
        ["src/App.jsx"],
        "JavaScript",
    )

    assert resolved is None


def test_resolves_python_absolute_import():
    resolved = resolve_one(
        "test/main.py",
        "app.services.auth",
        ["app/services/auth.py"],
        "Python",
    )

    assert resolved == 1


def test_resolves_python_import_when_project_root_is_nested():
    resolved = resolve_one(
        "backend/app/api/users.py",
        "app.services.auth",
        ["backend/app/services/auth.py"],
        "Python",
    )

    assert resolved == 1


def test_resolves_python_relative_import():
    resolved = resolve_one(
        "app/routes.py",
        ".models",
        ["app/models.py"],
        "Python",
    )

    assert resolved == 1


def test_resolves_python_package_import():
    resolved = resolve_one(
        "app/main.py",
        "app.services",
        ["app/services/__init__.py"],
        "Python",
    )

    assert resolved == 1


def test_leaves_external_python_packages_unresolved():
    resolved = resolve_one(
        "app/main.py",
        "fastapi",
        ["app/services/auth.py"],
        "Python",
    )

    assert resolved is None


def test_analyze_project_resolves_cross_file_dependencies(
    db_session,
    tmp_path,
):
    """Regression test for the resolution pass running before a flush."""

    source_dir = tmp_path / "src"
    source_dir.mkdir()

    (source_dir / "main.jsx").write_text(
        'import App from "./App";\n',
        encoding="utf-8",
    )
    (source_dir / "App.jsx").write_text(
        "export default function App() { return null; }\n",
        encoding="utf-8",
    )

    project = Project(
        owner_id=1,
        name="Resolution Test",
        source_type="manual",
        root_path=str(tmp_path),
        status="ready",
    )
    db_session.add(project)
    db_session.flush()

    main_file = ProjectFile(
        project_id=project.id,
        filename="main.jsx",
        relative_path="src/main.jsx",
        extension=".jsx",
        language="JavaScript",
        size_bytes=(source_dir / "main.jsx").stat().st_size,
    )
    app_file = ProjectFile(
        project_id=project.id,
        filename="App.jsx",
        relative_path="src/App.jsx",
        extension=".jsx",
        language="JavaScript",
        size_bytes=(source_dir / "App.jsx").stat().st_size,
    )

    db_session.add_all([main_file, app_file])
    db_session.flush()

    result = analyze_project(db_session, project)

    assert result["total_dependencies"] == 1
    assert result["resolved_dependencies"] == 1

    dependency = db_session.query(Dependency).filter(
        Dependency.project_id == project.id
    ).one()

    assert dependency.dependency_name == "./App"
    assert dependency.resolved_file_id == app_file.id


def test_analyze_project_keeps_external_dependencies_unresolved(
    db_session,
    tmp_path,
):
    source_dir = tmp_path / "src"
    source_dir.mkdir()

    (source_dir / "main.jsx").write_text(
        'import React from "react";\n'
        'import App from "./App";\n',
        encoding="utf-8",
    )
    (source_dir / "App.jsx").write_text(
        "export default function App() { return null; }\n",
        encoding="utf-8",
    )

    project = Project(
        owner_id=1,
        name="External Dependency Test",
        source_type="manual",
        root_path=str(tmp_path),
        status="ready",
    )
    db_session.add(project)
    db_session.flush()

    db_session.add_all([
        ProjectFile(
            project_id=project.id,
            filename="main.jsx",
            relative_path="src/main.jsx",
            extension=".jsx",
            language="JavaScript",
            size_bytes=(source_dir / "main.jsx").stat().st_size,
        ),
        ProjectFile(
            project_id=project.id,
            filename="App.jsx",
            relative_path="src/App.jsx",
            extension=".jsx",
            language="JavaScript",
            size_bytes=(source_dir / "App.jsx").stat().st_size,
        ),
    ])
    db_session.flush()

    analyze_project(db_session, project)

    dependencies = {
        dependency.dependency_name: dependency
        for dependency in db_session.query(Dependency).filter(
            Dependency.project_id == project.id
        ).all()
    }

    assert dependencies["react"].resolved_file_id is None
    assert dependencies["./App"].resolved_file_id is not None


def test_resolves_typescript_index_file():
    resolved = resolve_one(
        "src/main.ts",
        "./components",
        ["src/components/index.tsx"],
        "TypeScript",
    )

    assert resolved == 1


def test_resolves_typescript_relative_import():
    resolved = resolve_one(
        "src/pages/Home.tsx",
        "../components/Button",
        ["src/components/Button.tsx"],
        "TypeScript",
    )

    assert resolved == 1


def test_resolves_java_import_below_nested_source_root():
    resolved = resolve_one(
        "src/main/java/com/example/App.java",
        "com.example.service.UserService",
        ["src/main/java/com/example/service/UserService.java"],
        "Java",
    )

    assert resolved == 1


def test_leaves_external_java_import_unresolved():
    resolved = resolve_one(
        "src/main/java/com/example/App.java",
        "java.util.List",
        ["src/main/java/com/example/storage/List.java"],
        "Java",
    )

    assert resolved is None


def test_resolves_kotlin_import():
    resolved = resolve_one(
        "src/main/kotlin/com/example/App.kt",
        "com.example.models.User",
        ["src/main/kotlin/com/example/models/User.kt"],
        "Kotlin",
    )

    assert resolved == 1


def test_resolves_local_c_include():
    resolved = resolve_one(
        "src/main.c",
        "util/helpers.h",
        ["src/util/helpers.h"],
        "C",
        dependency_type="local_include",
    )

    assert resolved == 1


def test_resolves_relative_c_include():
    resolved = resolve_one(
        "src/parser/main.c",
        "../util/helpers.h",
        ["src/util/helpers.h"],
        "C",
        dependency_type="local_include",
    )

    assert resolved == 1


def test_leaves_system_c_include_unresolved():
    resolved = resolve_one(
        "src/main.c",
        "stdio.h",
        ["src/util/helpers.h"],
        "C",
        dependency_type="system_include",
    )

    assert resolved is None


def test_resolves_go_package_import():
    resolved = resolve_one(
        "cmd/server/main.go",
        "example.com/app/internal/auth",
        ["internal/auth/auth.go"],
        "Go",
    )

    assert resolved == 1


def test_leaves_go_standard_library_import_unresolved():
    resolved = resolve_one(
        "cmd/server/main.go",
        "fmt",
        ["internal/auth/auth.go"],
        "Go",
    )

    assert resolved is None


def test_resolves_rust_module_import():
    resolved = resolve_one(
        "src/main.rs",
        "crate::services::auth::login",
        ["src/services/auth.rs"],
        "Rust",
    )

    assert resolved == 1


def test_resolves_rust_mod_file_import():
    resolved = resolve_one(
        "src/main.rs",
        "crate::services::auth",
        ["src/services/auth/mod.rs"],
        "Rust",
    )

    assert resolved == 1


def test_leaves_rust_standard_library_import_unresolved():
    resolved = resolve_one(
        "src/main.rs",
        "std::collections::HashMap",
        ["src/services/auth.rs"],
        "Rust",
    )

    assert resolved is None


def test_resolves_php_namespaced_import():
    resolved = resolve_one(
        "public/index.php",
        "App\\Models\\User",
        ["src/Models/User.php"],
        "PHP",
    )

    assert resolved == 1


def test_leaves_external_php_import_unresolved():
    resolved = resolve_one(
        "public/index.php",
        "Illuminate\\Support\\Collection",
        ["src/Models/User.php"],
        "PHP",
    )

    assert resolved is None


def test_resolves_ruby_relative_require():
    resolved = resolve_one(
        "app/main.rb",
        "helpers/format",
        ["app/helpers/format.rb"],
        "Ruby",
        dependency_type="require_relative",
    )

    assert resolved == 1


def test_resolves_ruby_require_from_lib_root():
    resolved = resolve_one(
        "app/main.rb",
        "foo/bar",
        ["lib/foo/bar.rb"],
        "Ruby",
        dependency_type="require",
    )

    assert resolved == 1


def test_leaves_external_ruby_require_unresolved():
    resolved = resolve_one(
        "app/main.rb",
        "json",
        ["lib/foo/bar.rb"],
        "Ruby",
        dependency_type="require",
    )

    assert resolved is None


def test_extracts_html_asset_and_template_dependencies():
    from app.services.analysis.parser_manager import analyze_file

    source = """
<html>
  <head>
    <link href="../static/style.css" rel="stylesheet">
    <script src="../static/navbar.js"></script>
    {% include 'navbar.html' %}
  </head>
</html>
"""

    result = analyze_file(source, "HTML")

    found = {
        (dependency["dependency_type"], dependency["dependency_name"])
        for dependency in result["dependencies"]
    }

    assert found == {
        ("stylesheet", "../static/style.css"),
        ("script", "../static/navbar.js"),
        ("template_include", "navbar.html"),
    }


def test_ignores_external_html_assets():
    from app.services.analysis.parser_manager import analyze_file

    source = """
<link rel="stylesheet" href="https://cdn.example.com/app.css">
<script src="//cdn.example.com/app.js"></script>
"""

    result = analyze_file(source, "HTML")

    assert result["dependencies"] == []


def test_extracts_css_import_dependencies():
    from app.services.analysis.parser_manager import analyze_file

    result = analyze_file('@import "theme.css";\n', "CSS")

    assert result["dependencies"] == [
        {
            "dependency_name": "theme.css",
            "dependency_type": "css_import",
            "line_number": 1,
            "imported_symbols": None,
        }
    ]


def test_resolves_html_stylesheet_relative_to_page():
    resolved = resolve_one(
        "templates/index.html",
        "../static/style.css",
        ["static/style.css"],
        "HTML",
        dependency_type="stylesheet",
    )

    assert resolved == 1


def test_resolves_html_root_relative_asset():
    resolved = resolve_one(
        "templates/gitabot.html",
        "/static/gitabot.css",
        ["static/gitabot.css"],
        "HTML",
        dependency_type="stylesheet",
    )

    assert resolved == 1


def test_resolves_html_template_include():
    resolved = resolve_one(
        "templates/index.html",
        "navbar.html",
        ["templates/navbar.html"],
        "HTML",
        dependency_type="template_include",
    )

    assert resolved == 1


def test_resolves_stylesheet_reference_with_query_string():
    resolved = resolve_one(
        "templates/index.html",
        "../static/style.css?v=2",
        ["static/style.css"],
        "HTML",
        dependency_type="stylesheet",
    )

    assert resolved == 1


def test_leaves_missing_html_asset_unresolved():
    resolved = resolve_one(
        "templates/index.html",
        "../static/missing.css",
        ["static/style.css"],
        "HTML",
        dependency_type="stylesheet",
    )

    assert resolved is None


def test_resolves_css_import_relative_to_stylesheet():
    resolved = resolve_one(
        "static/main.css",
        "theme.css",
        ["static/theme.css"],
        "CSS",
        dependency_type="css_import",
    )

    assert resolved == 1


def test_analyze_project_links_html_to_stylesheet_and_script(
    db_session,
    tmp_path,
):
    """HTML asset references must appear as resolved project links."""

    templates_dir = tmp_path / "templates"
    static_dir = tmp_path / "static"
    templates_dir.mkdir()
    static_dir.mkdir()

    (templates_dir / "index.html").write_text(
        "<html><head>\n"
        '<link href="../static/style.css" rel="stylesheet">\n'
        '<script src="../static/app.js"></script>\n'
        "</head></html>\n",
        encoding="utf-8",
    )
    (static_dir / "style.css").write_text(
        "body { color: #fff; }\n",
        encoding="utf-8",
    )
    (static_dir / "app.js").write_text(
        "console.log('ready');\n",
        encoding="utf-8",
    )

    project = Project(
        owner_id=1,
        name="HTML Assets Test",
        source_type="manual",
        root_path=str(tmp_path),
        status="ready",
    )
    db_session.add(project)
    db_session.flush()

    page = ProjectFile(
        project_id=project.id,
        filename="index.html",
        relative_path="templates/index.html",
        extension=".html",
        language="HTML",
        size_bytes=(templates_dir / "index.html").stat().st_size,
    )
    stylesheet = ProjectFile(
        project_id=project.id,
        filename="style.css",
        relative_path="static/style.css",
        extension=".css",
        language="CSS",
        size_bytes=(static_dir / "style.css").stat().st_size,
    )
    script = ProjectFile(
        project_id=project.id,
        filename="app.js",
        relative_path="static/app.js",
        extension=".js",
        language="JavaScript",
        size_bytes=(static_dir / "app.js").stat().st_size,
    )

    db_session.add_all([page, stylesheet, script])
    db_session.flush()

    result = analyze_project(db_session, project)

    assert result["total_dependencies"] == 2
    assert result["resolved_dependencies"] == 2

    dependencies = {
        dependency.dependency_name: dependency
        for dependency in db_session.query(Dependency).filter(
            Dependency.project_id == project.id
        ).all()
    }

    assert dependencies["../static/style.css"].dependency_type == "stylesheet"
    assert dependencies["../static/style.css"].resolved_file_id == stylesheet.id
    assert dependencies["../static/app.js"].dependency_type == "script"
    assert dependencies["../static/app.js"].resolved_file_id == script.id
