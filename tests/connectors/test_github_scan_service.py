"""GitHub Scan Service 단위 테스트."""

from app.connectors.github_scan_service import GitHubScanService


def test_attach_source_metadata() -> None:
    findings = [
        {
            "type": "SLACK_BOT_TOKEN",
            "file": "config/slack.env",
            "line_number": 12,
            "fingerprint": "fingerprint-value",
        }
    ]

    result = GitHubScanService._attach_source_metadata(
        findings=findings,
        scan_id="scan-001",
        repository="KoYejun/NHI_Project",
        branch_name="main",
        commit_sha="abc123",
    )

    assert len(result) == 1
    assert result[0]["scan_id"] == "scan-001"
    assert result[0]["source"]["source_type"] == "GITHUB"
    assert result[0]["source"]["repository"] == "KoYejun/NHI_Project"
    assert result[0]["source"]["branch"] == "main"
    assert result[0]["source"]["commit_sha"] == "abc123"


def test_attach_source_metadata_does_not_modify_original() -> None:
    original_finding = {
        "type": "AWS_ACCESS_KEY",
        "file": ".env",
    }

    GitHubScanService._attach_source_metadata(
        findings=[original_finding],
        scan_id="scan-001",
        repository="owner/repository",
        branch_name="main",
        commit_sha="abc123",
    )

    assert "scan_id" not in original_finding
    assert "source" not in original_finding


def test_scan_id_has_expected_prefix() -> None:
    scan_id = GitHubScanService._create_scan_id()

    assert scan_id.startswith("scan-")
