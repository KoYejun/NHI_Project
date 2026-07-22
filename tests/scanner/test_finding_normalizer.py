"""Scanner Finding 정규화 단위 테스트."""

from pathlib import Path

from app.dev1_scanner.finding_normalizer import (
    build_finding_id,
    infer_provider,
    normalize_file_path,
    normalize_finding,
    remove_raw_secret_fields,
)


def test_infer_slack_provider() -> None:
    assert infer_provider("SLACK_BOT_TOKEN") == "slack"


def test_infer_github_provider() -> None:
    assert infer_provider("GITHUB_PERSONAL_ACCESS_TOKEN") == "github"


def test_infer_aws_provider() -> None:
    assert infer_provider("AWS_ACCESS_KEY") == "aws"


def test_infer_unknown_provider() -> None:
    assert infer_provider("RANDOM_SECRET") == "unknown"


def test_remove_raw_secret_fields() -> None:
    finding = {
        "type": "SLACK_BOT_TOKEN",
        "secret_value": "actual-secret",
        "raw_secret": "actual-secret",
        "_secret_value": "actual-secret",
        "masked_value": "xoxb****1234",
    }

    result = remove_raw_secret_fields(finding)

    assert "secret_value" not in result
    assert "raw_secret" not in result
    assert "_secret_value" not in result
    assert result["masked_value"] == "xoxb****1234"


def test_normalize_relative_file_path(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / "repository"
    target_file = repository_root / "config" / "slack.env"

    target_file.parent.mkdir(parents=True)
    target_file.write_text(
        "SLACK_TOKEN=fake",
        encoding="utf-8",
    )

    result = normalize_file_path(
        target_file,
        repository_root=repository_root,
    )

    assert result == "config/slack.env"


def test_normalize_finding() -> None:
    repository_root = Path("C:/temp/repository")

    raw_finding = {
        "type": "SLACK_BOT_TOKEN",
        "file": "C:/temp/repository/config/slack.env",
        "line_number": "12",
        "masked": "xoxb********1234",
        "fingerprint": "abcdef1234567890",
        "scanner": "regex",
        "detection_line": "SLACK_TOKEN=xoxb********1234",
        "secret_value": "must-not-be-exposed",
    }

    result = normalize_finding(
        raw_finding,
        repository_root=repository_root,
        scan_id="scan-001",
        repository="KoYejun/NHI_Project",
        branch="main",
        commit_sha="commit-abc",
    )

    assert result["scan_id"] == "scan-001"
    assert result["detector"] == "REGEX"
    assert result["secret_type"] == "SLACK_BOT_TOKEN"
    assert result["provider"] == "slack"
    assert result["file_path"] == "config/slack.env"
    assert result["line_number"] == 12
    assert result["masked_value"] == "xoxb********1234"
    assert result["source"]["repository"] == "KoYejun/NHI_Project"
    assert result["validation"]["status"] == "UNVERIFIED"
    assert "secret_value" not in result


def test_build_finding_id_uses_fingerprint_prefix() -> None:
    finding_id = build_finding_id(
        fingerprint="abcdef1234567890",
        file_path="config/slack.env",
        line_number=12,
    )

    assert finding_id.startswith("finding-abcdef123456")
    assert finding_id.endswith("-12")

def test_remove_repository_prefix_from_relative_path() -> None:
    result = normalize_file_path(
        "repository/scripts/create_sample_project.py",
        repository_root="C:/temp/repository",
    )

    assert result == "scripts/create_sample_project.py"


def test_infer_provider_from_github_pat() -> None:
    assert infer_provider("GITHUB_PAT") == "github"


def test_infer_provider_from_slack_token() -> None:
    assert infer_provider("SLACK_TOKEN") == "slack"


def test_infer_provider_from_aws_access_key_id() -> None:
    assert infer_provider("AWS_ACCESS_KEY_ID") == "aws"


def test_high_entropy_provider_remains_unknown() -> None:
    assert infer_provider("HIGH_ENTROPY_STRING") == "unknown"