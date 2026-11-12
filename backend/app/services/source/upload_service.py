
import shutil
import uuid

from pathlib import Path
from fastapi import UploadFile

from app.core.config import settings
from app.services.source.zip_extractor import extract_zip_safely


MB = 1024 * 1024


async def upload_and_extract_project(
    uploaded_file: UploadFile,
    user_id: int
) -> tuple[Path, str]:
    """
    Save and safely extract an uploaded ZIP project.

    Returns:
        A tuple containing:
        - Extracted project directory
        - Unique project storage folder name
    """

    # Validate filename.
    if not uploaded_file.filename:
        raise ValueError("No file was selected.")

    if Path(uploaded_file.filename).suffix.lower() != ".zip":
        raise ValueError("Only ZIP files are supported.")

    # Create a unique storage folder.
    storage_id = uuid.uuid4().hex

    # Resolve the configured upload directory relative to backend.
    backend_dir = Path(__file__).resolve().parents[3]
    upload_root = backend_dir / settings.UPLOAD_DIR

    project_storage = upload_root / str(user_id) / storage_id

    zip_path = project_storage / "upload.zip"
    extraction_path = project_storage / "source"

    project_storage.mkdir(parents=True, exist_ok=False)

    try:
        # Save uploaded ZIP in chunks.
        uploaded_size = 0
        max_upload_size = settings.MAX_UPLOAD_SIZE_MB * MB

        with zip_path.open("wb") as destination:
            while True:
                chunk = await uploaded_file.read(1024 * 1024)

                if not chunk:
                    break

                uploaded_size += len(chunk)

                if uploaded_size > max_upload_size:
                    raise ValueError(
                        "Uploaded ZIP exceeds the maximum upload size."
                    )

                destination.write(chunk)

        if uploaded_size == 0:
            raise ValueError("Uploaded ZIP file is empty.")

        # Safely extract ZIP contents.
        extracted_project = extract_zip_safely(
            zip_path=zip_path,
            destination=extraction_path
        )

        # Remove the original ZIP after successful extraction.
        zip_path.unlink(missing_ok=True)

        return extracted_project, storage_id

    except Exception:
        # Remove incomplete upload data.
        shutil.rmtree(project_storage, ignore_errors=True)
        raise

    finally:
        await uploaded_file.close()
