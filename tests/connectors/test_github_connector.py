"""GitHub Connector 기본 단위 테스트."""

import pytest

from app.connectors.github_connector import GitHubConnector


def test_connector_provider_is_github() -> None:
    connector = GitHubConnector(token=None)

    assert connector.provider == "github"


def test_connector_metadata_without_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)

    connector = GitHubConnector(token=None)

    metadata = connector.get_metadata()

    assert metadata["provider"] == "github"
    assert metadata["api_url"] == "https://api.github.com"
    assert metadata["authenticated"] is False
    assert metadata["timeout_seconds"] == 10


def test_parse_valid_repository_name() -> None:
    owner, repository = GitHubConnector._parse_repository_name("KoYejun/NHI_Project")

    assert owner == "KoYejun"
    assert repository == "NHI_Project"


@pytest.mark.parametrize(
    "invalid_repository",
    [
        "",
        "NHI_Project",
        "owner/repository/extra",
        "https://github.com/KoYejun/NHI_Project",
        "/",
    ],
)
def test_parse_invalid_repository_name(
    invalid_repository: str,
) -> None:
    with pytest.raises(ValueError):
        GitHubConnector._parse_repository_name(invalid_repository)


def test_explicit_token_has_priority(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GITHUB_TOKEN", "environment-token")

    connector = GitHubConnector(token="explicit-token")

    assert connector.token == "explicit-token"


def test_environment_token_is_loaded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GITHUB_TOKEN", "environment-token")

    connector = GitHubConnector()

    assert connector.token == "environment-token"
