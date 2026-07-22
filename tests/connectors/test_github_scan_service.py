"""GitHub Scan Service 단위 테스트."""

from app.connectors.github_scan_service import GitHubScanService


def test_scan_id_has_expected_prefix() -> None:
    scan_id = GitHubScanService._create_scan_id()

    assert scan_id.startswith("scan-")
