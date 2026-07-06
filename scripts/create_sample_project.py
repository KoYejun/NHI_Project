from pathlib import Path

AWS_ACCESS_KEY = "AKIA" + "1234567890ABCDEF"
GITHUB_TOKEN = "ghp_" + "abcdefghijklmnopqrstuvwxyz1234567890"
CLIENT_SECRET = "sample_client_secret_" + "abcdefghijklmnopqrstuvwxyz"
BEARER_TOKEN = "sampleBearerToken" + "1234567890abcdef"


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def create_sample_project() -> None:
    sample_dir = Path("data/sample_project")
    sample_dir.mkdir(parents=True, exist_ok=True)

    write_file(
        sample_dir / ".env",
        "\n".join(
            [
                "APP_ENV=production",
                "DB_HOST=prod-db.internal",
                f"AWS_ACCESS_KEY_ID={AWS_ACCESS_KEY}",
                'DATABASE_PASSWORD="sample-password"',
                "",
            ]
        ),
    )

    write_file(
        sample_dir / "app.py",
        "\n".join(
            [
                'API_URL = "https://api.example.com"',
                "",
                "# 테스트용 가짜 토큰",
                f'GITHUB_TOKEN = "{GITHUB_TOKEN}"',
                "",
                "",
                "def call_api():",
                '    print("sample app")',
                "",
            ]
        ),
    )

    write_file(
        sample_dir / "config.yml",
        "\n".join(
            [
                "app:",
                "  name: sample-service",
                "  environment: dev",
                "",
                "oauth:",
                "  client_id: sample-client-id",
                f"  client_secret: {CLIENT_SECRET}",
                "",
            ]
        ),
    )

    write_file(
        sample_dir / "server.log",
        "\n".join(
            [
                "2026-07-05 10:22:10 INFO Server started",
                f"2026-07-05 10:22:11 DEBUG Authorization: Bearer {BEARER_TOKEN}",
                "2026-07-05 10:22:12 INFO Request completed",
                "",
            ]
        ),
    )

    write_file(
        sample_dir / "README.md",
        "\n".join(
            [
                "# Sample Project",
                "",
                "이 폴더는 NHI Secret Agent 데모용 샘플 프로젝트입니다.",
                "모든 Secret 값은 실제 키가 아닌 테스트용 가짜 값입니다.",
                "",
            ]
        ),
    )

    print("Sample project created at data/sample_project")


if __name__ == "__main__":
    create_sample_project()
