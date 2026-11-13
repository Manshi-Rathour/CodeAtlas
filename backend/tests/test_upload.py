import zipfile

import pytest

from app.services.source.zip_extractor import extract_zip_safely


def create_zip(zip_path, files):
    with zipfile.ZipFile(zip_path, "w") as archive:
        for filename, content in files.items():
            archive.writestr(filename, content)


def test_extract_valid_zip(tmp_path):
    zip_path = tmp_path / "valid.zip"
    destination = tmp_path / "extracted"

    create_zip(
        zip_path,
        {
            "main.py": "print('Hello CodeAtlas')",
            "src/app.py": "print('Application')",
        }
    )

    result = extract_zip_safely(zip_path, destination)

    assert result == destination
    assert (destination / "main.py").read_text() == "print('Hello CodeAtlas')"
    assert (destination / "src" / "app.py").exists()


def test_reject_invalid_zip(tmp_path):
    zip_path = tmp_path / "invalid.zip"
    destination = tmp_path / "extracted"

    zip_path.write_text("This is not a ZIP archive")

    with pytest.raises(ValueError, match="not a valid ZIP"):
        extract_zip_safely(zip_path, destination)


def test_reject_zip_slip_path(tmp_path):
    zip_path = tmp_path / "unsafe.zip"
    destination = tmp_path / "extracted"

    create_zip(
        zip_path,
        {
            "../outside.txt": "Malicious content"
        }
    )

    with pytest.raises(ValueError, match="Unsafe ZIP path"):
        extract_zip_safely(zip_path, destination)

    assert not (tmp_path / "outside.txt").exists()


def test_reject_absolute_zip_path(tmp_path):
    zip_path = tmp_path / "absolute.zip"
    destination = tmp_path / "extracted"

    create_zip(
        zip_path,
        {
            "/outside.txt": "Malicious content"
        }
    )

    with pytest.raises(ValueError, match="Unsafe ZIP path"):
        extract_zip_safely(zip_path, destination)


def test_reject_windows_drive_path(tmp_path):
    zip_path = tmp_path / "windows.zip"
    destination = tmp_path / "extracted"

    create_zip(
        zip_path,
        {
            "C:/outside.txt": "Malicious content"
        }
    )

    with pytest.raises(ValueError, match="Unsafe ZIP path"):
        extract_zip_safely(zip_path, destination)


def test_reject_file_exceeding_size_limit(tmp_path):
    zip_path = tmp_path / "large.zip"
    destination = tmp_path / "extracted"

    create_zip(
        zip_path,
        {
            "large.txt": "A" * 1024
        }
    )

    with pytest.raises(ValueError, match="File exceeds size limit"):
        extract_zip_safely(
            zip_path,
            destination,
            max_file_size_mb=0.0005,
        )


def test_reject_too_many_files(tmp_path):
    zip_path = tmp_path / "many.zip"
    destination = tmp_path / "extracted"

    create_zip(
        zip_path,
        {
            "one.txt": "one",
            "two.txt": "two",
        }
    )

    with pytest.raises(ValueError, match="too many files"):
        extract_zip_safely(
            zip_path,
            destination,
            max_files=1,
        )


def test_reject_existing_destination(tmp_path):
    zip_path = tmp_path / "valid.zip"
    destination = tmp_path / "extracted"

    create_zip(zip_path, {"main.py": "print('Hello')"})

    destination.mkdir()

    with pytest.raises(ValueError, match="already exists"):
        extract_zip_safely(zip_path, destination)


def test_reject_missing_zip_file(tmp_path):
    zip_path = tmp_path / "missing.zip"
    destination = tmp_path / "extracted"

    with pytest.raises(ValueError, match="does not exist"):
        extract_zip_safely(zip_path, destination)
