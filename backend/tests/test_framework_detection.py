import json

import pytest

from app.services.analysis.framework_detector import (
    detect_project_technologies,
)


def _write_manifest(project_root, relative_path, content):
    manifest = project_root / relative_path
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(content, encoding="utf-8")
    return manifest


def _register_manifest_file(file_factory, project_id, relative_path, language):
    return file_factory(
        project_id,
        relative_path,
        language=language,
    )


def test_detects_react_next_express_axios_and_postgres(
    tmp_path,
    register_user,
    project_factory,
    file_factory,
    db_session,
):
    user, _ = register_user("framework-node@example.com")
    project = project_factory(user.id, "Node Project")
    project.root_path = str(tmp_path)
    db_session.commit()

    package_json = {
        "dependencies": {
            "react": "^19.0.0",
            "react-dom": "^19.0.0",
            "next": "^15.0.0",
            "express": "^4.19.0",
            "axios": "^1.7.0",
            "pg": "^8.12.0",
        },
        "devDependencies": {"vitest": "^2.0.0"},
    }

    _write_manifest(
        tmp_path,
        "package.json",
        json.dumps(package_json),
    )

    _register_manifest_file(
        file_factory, project.id, "package.json", "JSON"
    )

    technologies = detect_project_technologies(
        db=db_session,
        project_id=project.id,
    )

    assert "JavaScript" not in technologies["languages"]
    assert set(technologies["frameworks"]) >= {
        "React",
        "Next.js",
        "Express.js",
    }
    assert "Axios" in technologies["libraries"]
    assert "PostgreSQL" in technologies["databases"]
    assert "Vitest" not in technologies["frameworks"]


def test_detects_python_fastapi_sqlalchemy_and_postgres(
    tmp_path,
    register_user,
    project_factory,
    file_factory,
    db_session,
):
    user, _ = register_user("framework-python@example.com")
    project = project_factory(user.id, "Python Project")
    project.root_path = str(tmp_path)
    db_session.commit()

    _write_manifest(
        tmp_path,
        "requirements.txt",
        "\n".join([
            "# Web framework",
            "fastapi==0.115.0",
            "uvicorn[standard]>=0.30",
            "sqlalchemy==2.0.35",
            "psycopg2-binary==2.9.9",
        ]),
    )

    _register_manifest_file(
        file_factory, project.id, "requirements.txt", "Other"
    )
    _register_manifest_file(
        file_factory, project.id, "app/main.py", "Python"
    )

    technologies = detect_project_technologies(
        db=db_session,
        project_id=project.id,
    )

    assert technologies["languages"] == ["Python"]
    assert "FastAPI" in technologies["frameworks"]
    assert "SQLAlchemy" in technologies["libraries"]
    assert "PostgreSQL" in technologies["databases"]


def test_detects_go_gin_and_postgres_from_go_mod(
    tmp_path,
    register_user,
    project_factory,
    file_factory,
    db_session,
):
    user, _ = register_user("framework-go@example.com")
    project = project_factory(user.id, "Go Project")
    project.root_path = str(tmp_path)
    db_session.commit()

    _write_manifest(
        tmp_path,
        "go.mod",
        """module example.com/app

go 1.22

require (
    github.com/gin-gonic/gin v1.10.0
    github.com/lib/pq v1.10.9
)
""",
    )

    _register_manifest_file(file_factory, project.id, "go.mod", "Other")
    _register_manifest_file(
        file_factory, project.id, "main.go", "Go"
    )

    technologies = detect_project_technologies(
        db=db_session,
        project_id=project.id,
    )

    assert technologies["languages"] == ["Go"]
    assert "Gin" in technologies["frameworks"]
    assert "PostgreSQL" in technologies["databases"]


def test_detects_php_laravel_from_composer_json(
    tmp_path,
    register_user,
    project_factory,
    file_factory,
    db_session,
):
    user, _ = register_user("framework-php@example.com")
    project = project_factory(user.id, "PHP Project")
    project.root_path = str(tmp_path)
    db_session.commit()

    _write_manifest(
        tmp_path,
        "composer.json",
        json.dumps({
            "require": {
                "php": "^8.2",
                "laravel/framework": "^11.0",
            }
        }),
    )

    _register_manifest_file(
        file_factory, project.id, "composer.json", "JSON"
    )

    technologies = detect_project_technologies(
        db=db_session,
        project_id=project.id,
    )

    assert "Laravel" in technologies["frameworks"]


def test_detects_ruby_on_rails_from_gemfile(
    tmp_path,
    register_user,
    project_factory,
    file_factory,
    db_session,
):
    user, _ = register_user("framework-ruby@example.com")
    project = project_factory(user.id, "Ruby Project")
    project.root_path = str(tmp_path)
    db_session.commit()

    _write_manifest(
        tmp_path,
        "Gemfile",
        """source "https://rubygems.org"

gem "rails", "~> 7.1"
gem "pg"
""",
    )

    _register_manifest_file(file_factory, project.id, "Gemfile", "Other")

    technologies = detect_project_technologies(
        db=db_session,
        project_id=project.id,
    )

    assert "Ruby on Rails" in technologies["frameworks"]
    assert "PostgreSQL" in technologies["databases"]


def test_detects_rust_actix_and_serde_from_cargo_toml(
    tmp_path,
    register_user,
    project_factory,
    file_factory,
    db_session,
):
    user, _ = register_user("framework-rust@example.com")
    project = project_factory(user.id, "Rust Project")
    project.root_path = str(tmp_path)
    db_session.commit()

    _write_manifest(
        tmp_path,
        "Cargo.toml",
        """[package]
name = "demo"
version = "0.1.0"

[dependencies]
actix-web = "4"
serde = { version = "1", features = ["derive"] }
tokio = { version = "1", features = ["full"] }
""",
    )

    _register_manifest_file(
        file_factory, project.id, "Cargo.toml", "TOML"
    )

    technologies = detect_project_technologies(
        db=db_session,
        project_id=project.id,
    )

    assert "Actix Web" in technologies["frameworks"]
    assert "Serde" in technologies["libraries"]
    assert "Tokio" in technologies["libraries"]


def test_detects_spring_boot_from_pom_xml(
    tmp_path,
    register_user,
    project_factory,
    file_factory,
    db_session,
):
    user, _ = register_user("framework-java@example.com")
    project = project_factory(user.id, "Java Project")
    project.root_path = str(tmp_path)
    db_session.commit()

    _write_manifest(
        tmp_path,
        "pom.xml",
        """<project>
  <dependencies>
    <dependency>
      <groupId>org.springframework.boot</groupId>
      <artifactId>spring-boot-starter-web</artifactId>
    </dependency>
  </dependencies>
</project>
""",
    )

    _register_manifest_file(
        file_factory, project.id, "pom.xml", "XML"
    )

    technologies = detect_project_technologies(
        db=db_session,
        project_id=project.id,
    )

    assert "Spring Boot" in technologies["frameworks"]


def test_detects_technologies_from_source_imports(
    register_user,
    project_factory,
    file_factory,
    dependency_factory,
    db_session,
):
    user, _ = register_user("framework-imports@example.com")
    project = project_factory(user.id, "Import Detection Project")

    main = file_factory(project.id, "app/main.py", language="Python")

    dependency_factory(
        project_id=project.id,
        file_id=main.id,
        dependency_name="flask",
    )
    dependency_factory(
        project_id=project.id,
        file_id=main.id,
        dependency_name="redis",
    )

    technologies = detect_project_technologies(
        db=db_session,
        project_id=project.id,
    )

    assert "Flask" in technologies["frameworks"]
    assert "Redis" in technologies["databases"]


def test_missing_manifests_do_not_invent_technologies(
    register_user,
    project_factory,
    file_factory,
    dependency_factory,
    db_session,
):
    user, _ = register_user("framework-none@example.com")
    project = project_factory(user.id, "Plain Project")

    main = file_factory(project.id, "main.py", language="Python")
    dependency_factory(
        project_id=project.id,
        file_id=main.id,
        dependency_name="os",
    )

    technologies = detect_project_technologies(
        db=db_session,
        project_id=project.id,
    )

    assert technologies == {
        "languages": ["Python"],
        "frameworks": [],
        "libraries": [],
        "databases": [],
    }


def test_unsupported_dependencies_are_not_reported(
    tmp_path,
    register_user,
    project_factory,
    file_factory,
    db_session,
):
    user, _ = register_user("framework-unknown@example.com")
    project = project_factory(user.id, "Unknown Project")
    project.root_path = str(tmp_path)
    db_session.commit()

    _write_manifest(
        tmp_path,
        "package.json",
        json.dumps({
            "dependencies": {
                "socket.io": "^4.0.0",
                "some-random-tool": "^1.0.0",
            }
        }),
    )

    _register_manifest_file(
        file_factory, project.id, "package.json", "JSON"
    )

    technologies = detect_project_technologies(
        db=db_session,
        project_id=project.id,
    )

    assert technologies["frameworks"] == []
    assert technologies["libraries"] == []
    assert technologies["databases"] == []


def test_malformed_manifest_is_ignored(
    tmp_path,
    register_user,
    project_factory,
    file_factory,
    db_session,
):
    user, _ = register_user("framework-broken@example.com")
    project = project_factory(user.id, "Broken Manifest Project")
    project.root_path = str(tmp_path)
    db_session.commit()

    _write_manifest(
        tmp_path,
        "package.json",
        "{ this is not valid json",
    )

    _register_manifest_file(
        file_factory, project.id, "package.json", "JSON"
    )

    technologies = detect_project_technologies(
        db=db_session,
        project_id=project.id,
    )

    assert technologies["frameworks"] == []


def test_analysis_endpoint_includes_detected_technologies(
    tmp_path,
    client,
    register_user,
    project_factory,
    file_factory,
    db_session,
):
    user, headers = register_user("framework-endpoint@example.com")
    project = project_factory(user.id, "Technology Endpoint Project")
    project.root_path = str(tmp_path)
    db_session.commit()

    _write_manifest(
        tmp_path,
        "package.json",
        json.dumps({"dependencies": {"react": "^19.0.0"}}),
    )

    _register_manifest_file(
        file_factory, project.id, "package.json", "JSON"
    )
    _register_manifest_file(
        file_factory, project.id, "src/App.jsx", "JavaScript"
    )

    response = client.get(
        f"/api/projects/{project.id}/analysis",
        headers=headers,
    )

    assert response.status_code == 200

    technologies = response.json()["technologies"]

    assert "React" in technologies["frameworks"]
    assert "JavaScript" in technologies["languages"]
