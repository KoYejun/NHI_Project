from pathlib import Path

AWS_ACCESS_KEY = "AKIA" + "1234567890ABCDEF"
GITHUB_TOKEN = "ghp_" + "abcdefghijklmnopqrstuvwxyz1234567890"
CLIENT_SECRET = "sample_client_secret_" + "abcdefghijklmnopqrstuvwxyz"
BEARER_TOKEN = "sampleBearerToken" + "1234567890abcdef"

RAW_SECRETS = [
    AWS_ACCESS_KEY,
    GITHUB_TOKEN,
    CLIENT_SECRET,
    BEARER_TOKEN,
]


def create_sample_project(base_path: Path, relative_path: str = "sample_project") -> Path:
    sample_project = base_path / relative_path
    sample_project.mkdir(parents=True, exist_ok=True)

    (sample_project / ".env").write_text(
        "\n".join(
            [
                "APP_ENV=production",
                "DB_HOST=prod-db.internal",
                f"AWS_ACCESS_KEY_ID={AWS_ACCESS_KEY}",
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
                f'GITHUB_TOKEN = "{GITHUB_TOKEN}"',
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
                f"  client_secret: {CLIENT_SECRET}",
            ]
        ),
        encoding="utf-8",
    )

    (sample_project / "server.log").write_text(
        "\n".join(
            [
                "2026-07-05 10:22:10 INFO Server started",
                f"2026-07-05 10:22:11 DEBUG Authorization: Bearer {BEARER_TOKEN}",
                "2026-07-05 10:22:12 INFO Request completed",
            ]
        ),
        encoding="utf-8",
    )

    return sample_project
