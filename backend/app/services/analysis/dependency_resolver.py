from pathlib import PurePosixPath
from app.models.dependency import Dependency
from app.models.project_file import ProjectFile


def resolve_dependencies(
    dependencies: list[Dependency],
    project_files: list[ProjectFile],
) -> int:
    """
    Resolve local Python and JavaScript/TypeScript
    dependencies to files within the same project.

    External packages remain unresolved.
    """

    file_lookup = {}

    # Create a lookup of project file paths.
    for project_file in project_files:
        path = PurePosixPath(
            project_file.relative_path.replace("\\", "/")
        )

        file_lookup[str(path)] = project_file.id

    print("PROJECT FILE PATHS:", list(file_lookup.keys()))

    resolved_count = 0

    for dependency in dependencies:

        # Reset any previous resolution.
        dependency.resolved_file_id = None

        source_file = next(
            (
                file for file in project_files
                if file.id == dependency.file_id
            ),
            None
        )

        if source_file is None:
            continue

        source_path = PurePosixPath(
            source_file.relative_path.replace("\\", "/")
        )

        language = source_file.language.lower()
        dependency_name = dependency.dependency_name

        candidates = []

        # Python imports:
        # from services.auth import login
        # import services.auth
        if language == "python":

            module_path = dependency_name.replace(".", "/")

            print("DEPENDENCY:", dependency_name)
            print("CANDIDATES:", [
                f"{module_path}.py",
                f"{module_path}/__init__.py",
            ])

            candidates.extend([
                f"{module_path}.py",
                f"{module_path}/__init__.py",
            ])

        # JavaScript and TypeScript imports:
        # import Button from "./components/Button"
        elif language in ("javascript", "typescript", "tsx"):

            if not dependency_name.startswith((".", "/")):
                continue

            base_path = (
                source_path.parent / dependency_name
            )

            base_path = PurePosixPath(
                str(base_path)
            )

            candidates.append(str(base_path))

            extensions = [
                ".js",
                ".jsx",
                ".ts",
                ".tsx",
                ".mjs",
                ".cjs",
            ]

            for extension in extensions:
                candidates.append(
                    str(base_path) + extension
                )

            for extension in extensions:
                candidates.append(
                    str(base_path / ("index" + extension))
                )

        else:
            continue

        # Find the first matching project file.
        for candidate in candidates:

            resolved_id = file_lookup.get(candidate)

            if resolved_id is not None:
                dependency.resolved_file_id = resolved_id
                resolved_count += 1
                break

    return resolved_count
