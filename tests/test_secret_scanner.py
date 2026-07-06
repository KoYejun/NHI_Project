from pathlib import Path

from app.scanner.secret_scanner import scan_directory


def create_sample_project(base_path: Path) -> Path:
    sample_project = base_path / "sample_project"
    sample_project.mkdir()

    (sample_project / ".env").write_text(
        "\n".join(
            [
                "APP_ENV=production",
                "DB_HOST=prod-db.internal",
                "AWS_ACCESS_KEY_ID=AKIA1234567890ABCDEF",
                'DATABASE_PASSWORD="sample-password"',
            ]
        ),
        encoding="utf-8",
    )

    (sample_project / "app.py").write_text(
        "\n".join(
            [
                'API_URL = "https://api.example.com"',
                "",
                "# 테스트용 가짜 토큰",
                'GITHUB_TOKEN = "ghp_abcdefghijklmnopqrstuvwxyz1234567890"',
            ]
        ),
        encoding="utf-8",
    )

    (sample_project / "config.yml").write_text(
        "\n".join(
            [
                "app:",
                "  name: sample-service",
                "  environment: dev",
                "",
                "oauth:",
                "  client_id: sample-client-id",
                "  client_secret: sample_client_secret_abcdefghijklmnopqrstuvwxyz",
            ]
        ),
        encoding="utf-8",
    )

    (sample_project / "server.log").write_text(
        "\n".join(
            [
                "2026-07-05 10:22:10 INFO Server started",
                "2026-07-05 10:22:11 DEBUG Authorization: Bearer sampleBearerToken1234567890abcdef",
                "2026-07-05 10:22:12 INFO Request completed",
            ]
        ),
        encoding="utf-8",
    )

    return sample_project


def test_scan_directory_detects_expected_secret_types(tmp_path):
    sample_project = create_sample_project(tmp_path)

    findings = scan_directory(str(sample_project))

    secret_types = {finding["secret_type"] for finding in findings}

    assert len(findings) == 4
    assert "AWS_ACCESS_KEY_ID" in secret_types
    assert "GITHUB_TOKEN" in secret_types
    assert "GENERIC_CLIENT_SECRET" in secret_types
    assert "BEARER_TOKEN" in secret_types


def test_scan_directory_does_not_return_raw_secret_values(tmp_path):
    sample_project = create_sample_project(tmp_path)

    findings = scan_directory(str(sample_project))
    findings_text = str(findings)

    assert "AKIA1234567890ABCDEF" not in findings_text
    assert "ghp_abcdefghijklmnopqrstuvwxyz1234567890" not in findings_text
    assert "sample_client_secret_abcdefghijklmnopqrstuvwxyz" not in findings_text
    assert "sampleBearerToken1234567890abcdef" not in findings_text

    assert "raw_secret" not in findings_text
    assert "masked_secret" in findings_text
