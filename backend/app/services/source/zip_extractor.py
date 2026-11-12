
import shutil
import stat
import zipfile

from pathlib import Path, PurePosixPath, PureWindowsPath


# Maximum extracted content size: 500 MB
MAX_EXTRACTED_SIZE_MB = 500

# Maximum size of an individual extracted file: 50 MB
MAX_FILE_SIZE_MB = 50

# Maximum number of files in one project
MAX_FILES = 10000

# Convert MB into bytes
MB = 1024 * 1024


def extract_zip_safely(
    zip_path: Path,
    destination: Path,
    max_total_size_mb: int = MAX_EXTRACTED_SIZE_MB,
    max_file_size_mb: int = MAX_FILE_SIZE_MB,
    max_files: int = MAX_FILES
) -> Path:
    """
    Safely extract a ZIP archive into a destination directory.

    Security protections:
    1. Prevent path traversal (ZIP Slip).
    2. Reject symbolic links.
    3. Reject encrypted ZIP entries.
    4. Limit total extracted size.
    5. Limit individual file size.
    6. Limit the number of files.
    7. Clean up partial extraction on failure.

    Returns:
        Path: The extracted project directory.

    Raises:
        ValueError: If the archive is invalid or unsafe.
    """

    zip_path = Path(zip_path)
    destination = Path(destination)

    if not zip_path.is_file():
        raise ValueError("ZIP archive does not exist.")

    if not zipfile.is_zipfile(zip_path):
        raise ValueError("The uploaded file is not a valid ZIP archive.")

    if destination.exists():
        raise ValueError(
            "Extraction destination already exists."
        )

    if min(max_total_size_mb, max_file_size_mb, max_files) <= 0:
        raise ValueError("Extraction limits must be positive.")

    max_total_size = max_total_size_mb * MB
    max_file_size = max_file_size_mb * MB

    extracted_size = 0
    extracted_files = 0

    # Create the destination directory.
    destination.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    destination.mkdir()

    try:

        with zipfile.ZipFile(zip_path, "r") as archive:

            members = archive.infolist()

            for member in members:

                # Reject encrypted files.
                if member.flag_bits & 0x1:
                    raise ValueError(
                        "Encrypted ZIP files are not supported."
                    )

                # Normalize ZIP paths to prevent traversal.
                normalized_name = member.filename.replace("\\", "/")

                relative_path = PurePosixPath(normalized_name)
                windows_path = PureWindowsPath(normalized_name)

                # Reject absolute paths and Windows drive paths.
                if (
                    relative_path.is_absolute()
                    or windows_path.is_absolute()
                    or windows_path.drive
                    or ".." in relative_path.parts
                ):
                    raise ValueError(
                        f"Unsafe ZIP path detected: {member.filename}"
                    )

                # Ignore empty or current-directory entries.
                if not relative_path.parts:
                    continue

                # Reject symbolic links.
                unix_mode = member.external_attr >> 16

                if stat.S_ISLNK(unix_mode):
                    raise ValueError(
                        f"Symbolic links are not allowed: {member.filename}"
                    )

                # Resolve the final extraction path.
                target_path = destination.joinpath(
                    *relative_path.parts
                ).resolve()

                safe_root = destination.resolve()

                # Ensure the extracted path remains inside destination.
                if not target_path.is_relative_to(safe_root):
                    raise ValueError(
                        f"ZIP path escapes extraction directory: {member.filename}"
                    )

                # Create directories.
                if member.is_dir():
                    target_path.mkdir(
                        parents=True,
                        exist_ok=True
                    )
                    continue

                # Reject unsupported special file types.
                if stat.S_ISCHR(unix_mode) or stat.S_ISBLK(unix_mode):
                    raise ValueError(
                        f"Special files are not allowed: {member.filename}"
                    )

                if stat.S_ISFIFO(unix_mode) or stat.S_ISSOCK(unix_mode):
                    raise ValueError(
                        f"Special files are not allowed: {member.filename}"
                    )

                # Check individual file size.
                if member.file_size > max_file_size:
                    raise ValueError(
                        f"File exceeds size limit: {member.filename}"
                    )

                # Check total uncompressed size.
                extracted_size += member.file_size

                if extracted_size > max_total_size:
                    raise ValueError(
                        "ZIP archive exceeds total extraction size limit."
                    )

                # Check number of files.
                extracted_files += 1

                if extracted_files > max_files:
                    raise ValueError(
                        "ZIP archive contains too many files."
                    )

                # Avoid suspiciously high compression ratios.
                if member.file_size > 0:

                    if member.compress_size == 0:
                        raise ValueError(
                            f"Suspicious compression detected: {member.filename}"
                        )

                    compression_ratio = (
                        member.file_size / member.compress_size
                    )

                    if compression_ratio > 1000:
                        raise ValueError(
                            f"Suspicious compression ratio: {member.filename}"
                        )

                # Create parent directories.
                target_path.parent.mkdir(
                    parents=True,
                    exist_ok=True
                )

                # Stream extraction instead of loading entire files into memory.
                with archive.open(member, "r") as source:

                    # Exclusive creation prevents overwriting duplicate paths.
                    with target_path.open("xb") as target:

                        copied_size = 0

                        while True:

                            chunk = source.read(1024 * 1024)

                            if not chunk:
                                break

                            copied_size += len(chunk)

                            if copied_size > max_file_size:
                                raise ValueError(
                                    f"Extracted file exceeds size limit: {member.filename}"
                                )

                            target.write(chunk)

                        # Verify actual extracted size.
                        if copied_size != member.file_size:
                            raise ValueError(
                                f"File size mismatch: {member.filename}"
                            )

        return destination

    except Exception:

        # Remove partially extracted content on failure.
        shutil.rmtree(
            destination,
            ignore_errors=True
        )

        raise
