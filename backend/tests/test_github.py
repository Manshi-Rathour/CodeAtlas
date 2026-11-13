import pytest

from unittest.mock import patch

from app.services.source.github_service import (
    parse_github_url,
    validate_branch,
)


@pytest.fixture(autouse=True)
def mock_hostname_validation():
    with patch(
        "app.services.source.github_service.validate_public_hostname"
    ):
        yield


# Valid GitHub URLs

def test_parse_valid_github_url():
    owner, repository = parse_github_url(
        "https://github.com/octocat/Hello-World"
    )

    assert owner == "octocat"
    assert repository == "Hello-World"


def test_parse_github_url_with_git_extension():
    owner, repository = parse_github_url(
        "https://github.com/octocat/Hello-World.git"
    )

    assert owner == "octocat"
    assert repository == "Hello-World"


# Invalid GitHub URLs

@pytest.mark.parametrize(
    "repository_url",
    [
        "",
        "http://github.com/octocat/Hello-World",
        "https://gitlab.com/octocat/Hello-World",
        "https://github.com/octocat",
        "https://github.com/octocat/Hello-World?tab=readme",
        "https://github.com/octocat/Hello-World#readme",
        "https://user:password@github.com/octocat/Hello-World",
        "https://github.com:8080/octocat/Hello-World",
        "https://github.com/octocat/invalid%20repo",
    ]
)
def test_parse_invalid_github_urls(repository_url):
    with pytest.raises(ValueError):
        parse_github_url(repository_url)


# Valid branch names

@pytest.mark.parametrize(
    "branch",
    [
        "main",
        "master",
        "develop",
        "feature/login",
        "release/v1.0",
    ]
)
def test_validate_valid_branch_names(branch):
    assert validate_branch(branch) == branch


# Invalid branch names

@pytest.mark.parametrize(
    "branch",
    [
        "",
        "-main",
        "/main",
        "../main",
        "feature/",
        "feature//login",
        "feature name",
        "feature~1",
        "feature^1",
        "feature:login",
        "feature?login",
        "feature*login",
        "feature[login",
        "feature\\login",
    ]
)
def test_validate_invalid_branch_names(branch):
    with pytest.raises(ValueError):
        validate_branch(branch)
