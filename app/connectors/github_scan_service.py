"""GitHub Repository 수집과 Secret Scanner 실행을 연결한다."""

from __future__ import annotations

import tempfile
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.connectors.github_connector import GitHubConnector
from app.dev1_scanner.run_scan import run_detection


class GitHubScanService:
    """GitHub Repository를 Clone하고 기존 Scanner를 실행한다."""

    def __init__(
        self,
        connector: GitHubConnector | None = None,
    ) -> None:
        self.connector = connector or GitHubConnector()

    def scan_repository(
        self,
        repository: str,
        branch_name: str,
    ) -> dict[str, Any]:
        """
        GitHub Repository의 특정 Branch를 검사한다.

        처리 순서:
            1. 임시 폴더 생성
            2. Repository Clone
            3. Secret Scanner 실행
            4. GitHub 메타데이터 결합
            5. 임시 폴더 삭제
        """
        scan_id = self._create_scan_id()
        started_at = self._current_timestamp()

        with tempfile.TemporaryDirectory(prefix="nhi-secret-scan-") as temporary_directory:
            clone_path = Path(temporary_directory) / "repository"

            clone_result = self.connector.clone_repository(
                repository=repository,
                branch_name=branch_name,
                destination=clone_path,
            )

            findings = run_detection(clone_path)

            normalized_findings = self._attach_source_metadata(
                findings=findings,
                scan_id=scan_id,
                repository=repository,
                branch_name=branch_name,
                commit_sha=clone_result.get("commit_sha", ""),
            )

        completed_at = self._current_timestamp()

        detector_counts = Counter(str(finding.get("detector", "UNKNOWN")).upper() for finding in normalized_findings)

        provider_counts = Counter(str(finding.get("provider", "unknown")).lower() for finding in normalized_findings)

        return {
            "scan": {
                "scan_id": scan_id,
                "source_type": "GITHUB",
                "repository": repository,
                "branch": branch_name,
                "commit_sha": clone_result.get("commit_sha", ""),
                "started_at": started_at,
                "completed_at": completed_at,
                "status": "COMPLETED",
            },
            "summary": {
                "findings_total": len(normalized_findings),
                "detector_counts": dict(detector_counts),
                "provider_counts": dict(provider_counts),
            },
            "findings": normalized_findings,
        }

    @staticmethod
    def _attach_source_metadata(
        *,
        findings: list[dict[str, Any]],
        scan_id: str,
        repository: str,
        branch_name: str,
        commit_sha: str,
    ) -> list[dict[str, Any]]:
        """Scanner Finding에 GitHub 출처 정보를 결합한다."""
        normalized_findings: list[dict[str, Any]] = []

        for finding in findings:
            normalized_finding = dict(finding)

            normalized_finding["scan_id"] = scan_id
            normalized_finding["source"] = {
                "source_type": "GITHUB",
                "repository": repository,
                "branch": branch_name,
                "commit_sha": commit_sha,
            }

            normalized_findings.append(normalized_finding)

        return normalized_findings

    @staticmethod
    def _create_scan_id() -> str:
        """충돌 가능성이 낮은 Scan ID를 생성한다."""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        random_suffix = uuid4().hex[:8]

        return f"scan-{timestamp}-{random_suffix}"

    @staticmethod
    def _current_timestamp() -> str:
        """초 단위 ISO 8601 시간을 반환한다."""
        return datetime.now().isoformat(timespec="seconds")
