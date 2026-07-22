"""GitHub Repository Clone 기능 단위 테스트."""

from pathlib import Path
from unittest.mock import Mock

import pytest

from app.connectors.connector_errors import RepositoryCloneError
from app.connectors.github_connector import GitHubConnector


def test_clone_rejects_invalid_depth(
    tmp_path: Path,
) -> None:
    connector = GitHubConnector(token=None)

    with pytest.raises(ValueError):
        connector.clone_repository(
            repository="KoYejun/NHI_Project",
            branch_name="main",
            destination=tmp_path / "repository",
            depth=0,
        )


def test_clone_rejects_non_empty_destination(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connector = GitHubConnector(token=None)

    destination = tmp_path / "repository"
    destination.mkdir()
    (destination / "existing.txt").write_text(
        "existing",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        connector,
        "get_repository",
        Mock(return_value={"full_name": "KoYejun/NHI_Project"}),
    )
    monkeypatch.setattr(
        connector,
        "get_branch",
        Mock(
            return_value={
                "name": "main",
                "commit_sha": "abc123",
                "protected": False,
            }
        ),
    )

    with pytest.raises(RepositoryCloneError):
        connector.clone_repository(
            repository="KoYejun/NHI_Project",
            branch_name="main",
            destination=destination,
        )


def test_sanitize_empty_git_error() -> None:
    result = GitHubConnector._sanitize_git_error("")

    assert result == "상세 오류 메시지가 없습니다."


def test_sanitize_git_error_limits_length() -> None:
    error_message = "x" * 1000

    result = GitHubConnector._sanitize_git_error(error_message)

    assert len(result) == 500
