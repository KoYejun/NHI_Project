"""GitHub Connector를 수동으로 확인하는 실행 스크립트."""

from __future__ import annotations

import json
import sys

from app.connectors.connector_errors import ConnectorError
from app.connectors.github_connector import GitHubConnector

REPOSITORY = "KoYejun/NHI_Project"
TARGET_BRANCH = "full-dashboard-dev1-compatible"


def print_json(title: str, data: object) -> None:
    """데이터를 JSON 형태로 출력한다."""
    print()
    print("=" * 70)
    print(title)
    print("=" * 70)
    print(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
        )
    )


def main() -> int:
    connector = GitHubConnector()

    try:
        connection = connector.check_connection()
        print_json("1. GitHub 연결 상태", connection)

        repository = connector.get_repository(REPOSITORY)
        print_json("2. Repository 정보", repository)

        branches = connector.list_branches(REPOSITORY)
        print_json("3. Branch 목록", branches)

        target_branch = connector.get_branch(
            REPOSITORY,
            TARGET_BRANCH,
        )
        print_json("4. 대상 Branch 정보", target_branch)

    except ConnectorError as exc:
        print()
        print("[Connector 오류]")
        print(f"코드: {exc.error_code}")
        print(f"메시지: {exc.message}")
        return 1

    except ValueError as exc:
        print()
        print("[입력 오류]")
        print(str(exc))
        return 1

    print()
    print("GitHub Connector 기본 테스트를 완료했습니다.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
