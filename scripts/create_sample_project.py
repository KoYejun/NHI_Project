from pathlib import Path

SAMPLE_DIR = Path("data/sample_project")


def main() -> None:
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)

    aws_access_key = "AKIA" + "1234567890ABCDEF"
    aws_secret_key = "wJal" + "rXUtnFEMI/K7MDENG+bPxRfiCYEXAMPLEKEY"
    github_token = "ghp_" + "abcdefghijklmnopqrstuvwxyz1234567890"
    slack_token = "xoxb-" + "1234567890abcdefghijklmnopqrstuvwx"
    live_api_key = "sk_l" + "ive_abcdefghijklmnopqrstuvwxyzxxxx"
    bearer_token = "sampleBearerToken" + "1234567890abcdef"
    db_password = "Super" + "SecretPass123!"
    root_password = "root" + "A9b8C7d6E5f4G3h2I1j0k5d4e"
    client_secret = "cs_p" + "abcdefghijklmnopqrstuvwxyz12345b4c"
    generic_token = "tok_" + "abcdefghijklmnopqrstuvwxyz1234567890"
    readme_example_key = "example_" + "abcdefghijklmnopqrstuvwxyz7890"

    write_file(
        SAMPLE_DIR / ".env",
        f"""APP_ENV=production
DB_HOST=prod-db.internal
DB_USER=admin
DB_PASSWORD={db_password}
AWS_REGION=ap-northeast-2
AWS_ACCESS_KEY_ID={aws_access_key}
AWS_SECRET_ACCESS_KEY={aws_secret_key}
GITHUB_TOKEN={github_token}
""",
    )

    write_file(
        SAMPLE_DIR / "app.py",
        f'''API_URL = "https://api.example.com"

# GitHub Actions 배포 자동화 테스트용 가짜 값
GITHUB_TOKEN = "{github_token}"

def deploy():
    print("deploying service")

slack_bot_token = "{slack_token}"

def call_payment_api():
    # production privileged payment secret
    api_key = "{live_api_key}"
    return api_key

def connect_database():
    # database root password
    db_password = "{root_password}"
    return db_password
''',
    )

    write_file(
        SAMPLE_DIR / "config.yml",
        f"""app:
  name: sample-service
  app_env: production

database:
  host: prod-db.internal
  user: admin
  password: ChangeMe123!

oauth:
  client_secret: {client_secret}
  token: {generic_token}
""",
    )

    write_file(
        SAMPLE_DIR / "README.md",
        f"""# Sample Project

이 폴더는 NHI Secret Agent 데모용 샘플 프로젝트입니다.

아래 값은 문서 예시로 작성된 가짜 API Key입니다.

example_api_key={readme_example_key}
""",
    )

    write_file(
        SAMPLE_DIR / "server.log",
        f"""2026-07-01 10:22:10 INFO Server started
2026-07-01 10:22:15 DEBUG Authorization: Bearer {bearer_token}
2026-07-01 10:23:01 INFO Health check completed
2026-07-01 10:25:44 INFO production admin database backup job started
2026-07-01 10:25:45 INFO AWS_ACCESS_KEY_ID={aws_access_key} used for backup upload job
""",
    )

    write_file(SAMPLE_DIR / ".gitkeep", "")

    print(f"Sample project created: {SAMPLE_DIR.as_posix()}")


def write_file(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    main()
