"""GitHub Repository를 Clone하고 Secret Scanner를 실행한다."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from app.connectors.connector_errors import ConnectorError
from app.connectors.github_scan_service import GitHubScanService

DEFAULT_REPOSITORY = "KoYejun/NHI_Project"
DEFAULT_BRANCH = "full-dashboard-dev1-compatible"
DEFAULT_OUTPUT = Path("data/results/github_scan_result.json")


def parse_arguments() -> argparse.Namespace:
    """명령행 인자를 읽는다."""
    parser = argparse.ArgumentParser(
        description=("GitHub Repository의 특정 Branch를 내려받아 Secret Scanner를 실행합니다.")
    )

    parser.add_argument(
        "--repository",
        default=DEFAULT_REPOSITORY,
        help=(f"owner/repository 형식의 GitHub Repository. 기본값: {DEFAULT_REPOSITORY}"),
    )

    parser.add_argument(
        "--branch",
        default=DEFAULT_BRANCH,
        help=f"검사할 Branch. 기본값: {DEFAULT_BRANCH}",
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"결과 JSON 경로. 기본값: {DEFAULT_OUTPUT}",
    )

    return parser.parse_args()


def write_json(
    output_path: Path,
    data: dict[str, Any],
) -> None:
    """분석 결과를 UTF-8 JSON 파일로 저장한다."""
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def print_summary(result: dict[str, Any]) -> None:
    """터미널에 핵심 Scan 결과를 출력한다."""
    scan = result.get("scan", {})
    summary = result.get("summary", {})

    print()
    print("=" * 70)
    print("GitHub Repository Secret Scan 완료")
    print("=" * 70)
    print(f"Scan ID: {scan.get('scan_id')}")
    print(f"Repository: {scan.get('repository')}")
    print(f"Branch: {scan.get('branch')}")
    print(f"Commit SHA: {scan.get('commit_sha')}")
    print(f"Status: {scan.get('status')}")
    print(f"Finding 수: {summary.get('findings_total', 0)}")
    print(f"Detector별 결과: {summary.get('detector_counts', {})}")
    print(f"Provider별 결과: {summary.get('provider_counts', {})}")


def main() -> int:
    arguments = parse_arguments()

    service = GitHubScanService()

    try:
        result = service.scan_repository(
            repository=arguments.repository,
            branch_name=arguments.branch,
        )

        write_json(
            output_path=arguments.output,
            data=result,
        )

        print_summary(result)

        print()
        print(f"결과 파일: {arguments.output.resolve()}")

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

    except Exception as exc:
        print()
        print("[Scan 오류]")
        print(f"{type(exc).__name__}: {exc}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
