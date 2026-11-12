
import re
import shutil
import uuid
import ipaddress
import socket

from pathlib import Path
from urllib.parse import urlparse, quote, urljoin

import requests

from app.core.config import settings
from app.services.source.zip_extractor import extract_zip_safely


MB = 1024 * 1024

MAX_ARCHIVE_SIZE = 100 * MB
DOWNLOAD_TIMEOUT = (10, 60)

GITHUB_HOST = "github.com"
GITHUB_API_HOST = "api.github.com"


def validate_public_hostname(hostname: str) -> None:
    """
    Ensure the hostname resolves only to public IP addresses.
    """

    try:
        addresses = socket.getaddrinfo(
            hostname,
            None,
            type=socket.SOCK_STREAM
        )
    except socket.gaierror:
        raise ValueError("GitHub hostname could not be resolved.")

    if not addresses:
        raise ValueError("Invalid GitHub hostname.")

    for address in addresses:
        ip = ipaddress.ip_address(address[4][0])

        if not ip.is_global:
            raise ValueError("Private or non-public network addresses are not allowed.")


def parse_github_url(repository_url: str) -> tuple[str, str]:
    """
    Validate a public GitHub repository URL and extract owner and repository.
    """

    if not repository_url:
        raise ValueError("GitHub repository URL is required.")

    try:
        parsed = urlparse(repository_url.strip())
    except ValueError:
        raise ValueError("Invalid GitHub repository URL.")

    if parsed.scheme != "https":
        raise ValueError("Only HTTPS GitHub URLs are allowed.")

    if parsed.hostname != GITHUB_HOST:
        raise ValueError("Only public github.com repositories are supported.")

    if parsed.port not in (None, 443):
        raise ValueError("Custom ports are not allowed.")

    if parsed.username or parsed.password:
        raise ValueError("Credentials in GitHub URLs are not allowed.")

    if parsed.query or parsed.fragment:
        raise ValueError("Query parameters and fragments are not allowed.")

    validate_public_hostname(GITHUB_HOST)

    parts = parsed.path.strip("/").split("/")

    if len(parts) < 2:
        raise ValueError("Invalid GitHub repository URL.")

    owner, repository = parts[0], parts[1]

    if repository.endswith(".git"):
        repository = repository[:-4]

    valid_name = re.compile(r"^[A-Za-z0-9_.-]{1,100}$")

    if not valid_name.fullmatch(owner):
        raise ValueError("Invalid GitHub owner name.")

    if not valid_name.fullmatch(repository):
        raise ValueError("Invalid GitHub repository name.")

    return owner, repository


def validate_branch(branch: str) -> str:
    """
    Validate a branch name before using it in an archive URL.
    """

    if not branch or len(branch) > 255:
        raise ValueError("Invalid GitHub branch name.")

    if branch.startswith("-") or branch.startswith("/"):
        raise ValueError("Invalid GitHub branch name.")

    if (
        ".." in branch
        or branch.endswith("/")
        or branch.endswith(".")
        or "//" in branch
        or "@{" in branch
        or "\\" in branch
        or any(ord(char) < 32 or ord(char) == 127 for char in branch)
        or any(char in branch for char in (" ", "~", "^", ":", "?", "*", "["))
    ):
        raise ValueError("Invalid GitHub branch name.")

    return branch



def download_github_archive(
    owner: str,
    repository: str,
    branch: str,
    destination: Path
) -> None:
    """
    Download a public GitHub branch archive.

    Only allows HTTPS redirects between trusted GitHub hosts.
    Enforces redirect, timeout and download-size limits.
    """

    archive_url = (
        f"https://{GITHUB_HOST}/{owner}/{repository}"
        f"/archive/refs/heads/{quote(branch, safe='/')}.zip"
    )

    allowed_hosts = {
        "github.com",
        "codeload.github.com"
    }

    current_url = archive_url
    response = None
    max_redirects = 3

    try:
        for redirect_count in range(max_redirects + 1):

            parsed = urlparse(current_url)

            if (
                parsed.scheme != "https"
                or parsed.hostname not in allowed_hosts
                or parsed.port not in (None, 443)
                or parsed.username
                or parsed.password
            ):
                raise ValueError("Untrusted GitHub archive URL rejected.")

            validate_public_hostname(parsed.hostname)

            response = requests.get(
                current_url,
                stream=True,
                allow_redirects=False,
                timeout=DOWNLOAD_TIMEOUT
            )

            if response.status_code in (301, 302, 303, 307, 308):

                location = response.headers.get("Location")
                response.close()
                response = None

                if not location:
                    raise ValueError(
                        "GitHub returned an invalid redirect."
                    )

                if redirect_count >= max_redirects:
                    raise ValueError(
                        "Too many redirects while downloading repository."
                    )

                current_url = urljoin(current_url, location)
                continue

            if response.status_code == 404:
                raise ValueError(
                    "Repository or branch not found. "
                    "Check the URL and branch name."
                )

            if response.status_code == 403:
                raise ValueError("GitHub denied the archive request.")

            response.raise_for_status()

            break

        else:
            raise ValueError("Could not download GitHub repository.")

        content_length = response.headers.get("Content-Length")

        if content_length:
            try:
                if int(content_length) > MAX_ARCHIVE_SIZE:
                    raise ValueError(
                        "GitHub repository archive is too large."
                    )
            except ValueError as error:
                if str(error) == "GitHub repository archive is too large.":
                    raise

                raise ValueError("Invalid archive size returned by GitHub.")

        downloaded_size = 0

        with destination.open("xb") as archive_file:

            for chunk in response.iter_content(
                chunk_size=1024 * 1024
            ):
                if not chunk:
                    continue

                downloaded_size += len(chunk)

                if downloaded_size > MAX_ARCHIVE_SIZE:
                    raise ValueError(
                        "GitHub repository archive is too large."
                    )

                archive_file.write(chunk)

        if downloaded_size == 0:
            raise ValueError(
                "GitHub returned an empty repository archive."
            )

    finally:
        if response is not None:
            response.close()


def import_github_repository(
    repository_url: str,
    user_id: int,
    branch: str = "main"
) -> tuple[Path, str, str, str]:
    """
    Download and safely extract a public GitHub repository.

    Returns:
        extracted_path, storage_id, owner, repository
    """

    storage_id = uuid.uuid4().hex

    owner, repository = parse_github_url(repository_url)
    branch = validate_branch(branch)

    backend_dir = Path(__file__).resolve().parents[3]

    upload_root = backend_dir / settings.UPLOAD_DIR
    project_storage = upload_root / str(user_id) / storage_id

    archive_path = project_storage / "repository.zip"
    extraction_path = project_storage / "source"

    project_storage.mkdir(parents=True, exist_ok=False)

    try:
        download_github_archive(
            owner=owner,
            repository=repository,
            branch=branch,
            destination=archive_path
        )

        extracted_path = extract_zip_safely(
            zip_path=archive_path,
            destination=extraction_path
        )

        archive_path.unlink(missing_ok=True)

        # GitHub archives contain a top-level folder.
        entries = list(extracted_path.iterdir())

        if len(entries) == 1 and entries[0].is_dir():
            extracted_path = entries[0]

        return extracted_path, storage_id, owner, repository

    except Exception:
        shutil.rmtree(project_storage, ignore_errors=True)
        raise
