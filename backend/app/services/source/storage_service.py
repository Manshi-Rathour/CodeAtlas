import shutil

from pathlib import Path

from app.core.config import settings


def _upload_root() -> Path:
    """Resolve the configured upload directory inside the backend."""

    backend_dir = Path(__file__).resolve().parents[3]

    return (backend_dir / settings.UPLOAD_DIR).resolve()


def remove_project_storage(
    root_path: str | None,
    user_id: int,
) -> None:
    """
    Delete the imported source folder for a project.

    Only folders inside the configured upload directory and inside the
    owner's storage area are removed. Manual projects have no storage.
    """

    if not root_path:
        return

    upload_root = _upload_root()

    try:
        # Resolve without requiring the path to exist, so a storage folder
        # can still be removed if the source folder was moved or lost.
        project_root = Path(root_path).resolve()
        relative_parts = project_root.relative_to(upload_root).parts
    except (OSError, ValueError):
        return

    # Expected layout: <upload_root>/<user_id>/<storage_id>/...
    if (
        len(relative_parts) < 3
        or relative_parts[0] != str(user_id)
    ):
        return

    storage_folder = upload_root / relative_parts[0] / relative_parts[1]

    shutil.rmtree(storage_folder, ignore_errors=True)

    # Remove the owner's folder once it no longer holds any project.
    user_folder = upload_root / relative_parts[0]

    try:
        user_folder.rmdir()
    except OSError:
        # The folder is not empty or is already gone.
        pass


def remove_user_storage(user_id: int) -> None:
    """
    Delete every imported source folder belonging to a user.

    Used when an account is deleted. The path is resolved and must stay
    inside the upload directory.
    """

    upload_root = _upload_root()

    try:
        user_folder = (upload_root / str(user_id)).resolve()
    except (OSError, ValueError):
        return

    if user_folder == upload_root or not user_folder.is_relative_to(
        upload_root
    ):
        return

    shutil.rmtree(user_folder, ignore_errors=True)
