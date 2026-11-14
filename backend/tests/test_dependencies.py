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

    def __init__(self, file_id, dependency_name):
        self.file_id = file_id
        self.dependency_name = dependency_name
        self.resolved_file_id = None


def resolve_one(source_path, dependency_name, project_paths, language):
    source_id = 100
    files = [
        FakeFile(source_id, source_path, language)
    ]

    for index, path in enumerate(project_paths, start=1):
        files.append(
            FakeFile(index, path, language)
        )

    dependency = FakeDependency(source_id, dependency_name)

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
