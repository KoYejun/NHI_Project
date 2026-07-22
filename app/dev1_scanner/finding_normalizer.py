"""Scanner Finding을 팀원 간 공통 형식으로 정규화한다."""

from __future__ import annotations

from pathlib import Path
from typing import Any

PROVIDER_BY_SECRET_TYPE = {
    "SLACK_BOT_TOKEN": "slack",
    "SLACK_USER_TOKEN": "slack",
    "SLACK_APP_TOKEN": "slack",
    "SLACK_TOKEN": "slack",

    "GITHUB_PERSONAL_ACCESS_TOKEN": "github",
    "GITHUB_FINE_GRAINED_PAT": "github",
    "GITHUB_PAT": "github",
    "GITHUB_TOKEN": "github",
    "GITHUB_OAUTH_TOKEN": "github",

    "AWS_ACCESS_KEY": "aws",
    "AWS_ACCESS_KEY_ID": "aws",
    "AWS_SECRET_ACCESS_KEY": "aws",
    "AWS_SESSION_TOKEN": "aws",

    "GOOGLE_API_KEY": "google",
    "GOOGLE_OAUTH_TOKEN": "google",
    "GCP_SERVICE_ACCOUNT": "google",

    "AZURE_CLIENT_SECRET": "azure",

    "GITLAB_TOKEN": "gitlab",
    "NOTION_TOKEN": "notion",
    "HUGGING_FACE_TOKEN": "huggingface",
    "HUGGINGFACE_TOKEN": "huggingface",

    "DATABASE_URL": "database",
    "DB_CREDENTIAL": "database",
    "POSTGRES_URL": "database",
    "MYSQL_URL": "database",
    "MONGODB_URI": "database",

    "JWT": "generic",
    "PRIVATE_KEY": "generic",

    "HIGH_ENTROPY_STRING": "unknown",
    "HIGH_ENTROPY": "unknown",
    "GENERIC_API_KEY": "unknown",
    "GENERIC_SECRET": "unknown",
}


RAW_SECRET_KEYS = {
    "secret",
    "secret_value",
    "raw_secret",
    "raw_value",
    "token",
    "credential",
    "_secret_value",
}


def normalize_finding(
    finding: dict[str, Any],
    *,
    repository_root: str | Path,
    scan_id: str,
    repository: str,
    branch: str,
    commit_sha: str,
) -> dict[str, Any]:
    """
    Scanner 결과 한 건을 공통 Finding 형식으로 변환한다.

    Args:
        finding:
            기존 Regex 또는 Entropy Scanner 결과.
        repository_root:
            Clone된 Repository의 로컬 루트 경로.
        scan_id:
            현재 Scan 실행 ID.
        repository:
            owner/repository 형식의 GitHub Repository.
        branch:
            검사한 Branch.
        commit_sha:
            검사한 Commit SHA.

    Returns:
        팀원 2와 팀원 3이 사용할 공통 Finding 데이터.
    """
    sanitized_finding = remove_raw_secret_fields(finding)

    secret_type = _first_non_empty(
        sanitized_finding,
        "secret_type",
        "type",
        "pattern_id",
    )
    secret_type = str(secret_type or "UNKNOWN_SECRET").upper()

    detector = _normalize_detector(
        _first_non_empty(
            sanitized_finding,
            "detector",
            "scanner",
            "detection_method",
            "source",
        )
    )

    file_value = _first_non_empty(
        sanitized_finding,
        "file_path",
        "file",
        "path",
    )

    file_path = normalize_file_path(
        file_value,
        repository_root=repository_root,
    )

    line_number = _normalize_line_number(
        _first_non_empty(
            sanitized_finding,
            "line_number",
            "line",
            "line_no",
        )
    )

    masked_value = _first_non_empty(
        sanitized_finding,
        "masked_value",
        "masked",
        "masked_secret",
    )

    detection_line = _first_non_empty(
        sanitized_finding,
        "detection_line",
        "line_content",
        "matched_line",
        "context",
    )

    fingerprint = _first_non_empty(
        sanitized_finding,
        "fingerprint",
        "secret_fingerprint",
        "hash",
    )

    provider = _first_non_empty(
        sanitized_finding,
        "provider",
    )

    if not provider:
        provider = infer_provider(secret_type)

    context_before = _normalize_context_lines(sanitized_finding.get("context_before"))
    context_after = _normalize_context_lines(sanitized_finding.get("context_after"))

    normalized = {
        "finding_id": build_finding_id(
            fingerprint=str(fingerprint or ""),
            file_path=file_path,
            line_number=line_number,
        ),
        "scan_id": scan_id,
        "detector": detector,
        "secret_type": secret_type,
        "provider": str(provider).lower(),
        "masked_value": str(masked_value or ""),
        "fingerprint": str(fingerprint or ""),
        "file_path": file_path,
        "line_number": line_number,
        "detection_line": str(detection_line or ""),
        "context_before": context_before,
        "context_after": context_after,
        "source": {
            "source_type": "GITHUB",
            "repository": repository,
            "branch": branch,
            "commit_sha": commit_sha,
        },
        "validation": {
            "status": "UNVERIFIED",
            "provider": str(provider).lower(),
            "raw_scopes": [],
        },
        "metadata": {
            "original_keys": sorted(sanitized_finding.keys()),
        },
    }

    validate_normalized_finding(normalized)

    return normalized


def normalize_findings(
    findings: list[dict[str, Any]],
    *,
    repository_root: str | Path,
    scan_id: str,
    repository: str,
    branch: str,
    commit_sha: str,
) -> list[dict[str, Any]]:
    """Scanner Finding 목록 전체를 공통 형식으로 변환한다."""
    return [
        normalize_finding(
            finding,
            repository_root=repository_root,
            scan_id=scan_id,
            repository=repository,
            branch=branch,
            commit_sha=commit_sha,
        )
        for finding in findings
    ]


def remove_raw_secret_fields(
    finding: dict[str, Any],
) -> dict[str, Any]:
    """원본 Secret일 가능성이 있는 필드를 출력 데이터에서 제거한다."""
    sanitized = dict(finding)

    for key in RAW_SECRET_KEYS:
        sanitized.pop(key, None)

    return sanitized


def normalize_file_path(
    file_value: object,
    *,
    repository_root: str | Path,
) -> str:
    """파일 경로를 Repository 루트 기준 상대경로로 변환한다."""
    if file_value is None:
        return ""

    normalized = str(file_value).replace("\\", "/").strip()
    normalized = normalized.lstrip("./")

    if normalized.startswith("repository/"):
        normalized = normalized.removeprefix("repository/")

    raw_path = Path(str(file_value))
    root_path = Path(repository_root).resolve()

    try:
        resolved_path = raw_path.resolve()
        relative_path = resolved_path.relative_to(root_path)

        relative_normalized = relative_path.as_posix()

        if relative_normalized.startswith("repository/"):
            return relative_normalized.removeprefix("repository/")

        return relative_normalized

    except (OSError, ValueError):
        repository_marker = "/repository/"

        if repository_marker in normalized:
            return normalized.split(repository_marker, maxsplit=1)[1]

        return normalized


def infer_provider(secret_type: str) -> str:
    """Secret 유형을 기반으로 Provider를 추론한다."""
    normalized_type = (
        secret_type.upper()
        .replace("-", "_")
        .replace(" ", "_")
    )

    direct_provider = PROVIDER_BY_SECRET_TYPE.get(normalized_type)

    if direct_provider:
        return direct_provider

    if "SLACK" in normalized_type or "XOXB" in normalized_type:
        return "slack"

    if (
        "GITHUB" in normalized_type
        or normalized_type.startswith("GHP")
        or "GH_PAT" in normalized_type
    ):
        return "github"

    if (
        "AWS" in normalized_type
        or "AMAZON" in normalized_type
        or "AKIA" in normalized_type
    ):
        return "aws"

    if (
        "GOOGLE" in normalized_type
        or "GCP" in normalized_type
    ):
        return "google"

    if (
        "AZURE" in normalized_type
        or "MICROSOFT" in normalized_type
    ):
        return "azure"

    if "GITLAB" in normalized_type:
        return "gitlab"

    if "NOTION" in normalized_type:
        return "notion"

    if "HUGGINGFACE" in normalized_type or "HUGGING_FACE" in normalized_type:
        return "huggingface"

    if (
        "DATABASE" in normalized_type
        or normalized_type.startswith("DB_")
        or "POSTGRES" in normalized_type
        or "MYSQL" in normalized_type
        or "MONGODB" in normalized_type
    ):
        return "database"

    return "unknown"


def build_finding_id(
    *,
    fingerprint: str,
    file_path: str,
    line_number: int,
) -> str:
    """
    Finding 위치를 구분할 수 있는 식별자를 생성한다.

    Fingerprint 전체를 노출하지 않도록 앞 12자리만 사용한다.
    """
    fingerprint_prefix = fingerprint[:12] if fingerprint else "no-fingerprint"

    safe_path = file_path.replace("/", "-").replace("\\", "-").replace(" ", "-")

    return f"finding-{fingerprint_prefix}-{safe_path}-{line_number}"


def validate_normalized_finding(
    finding: dict[str, Any],
) -> None:
    """공통 Finding에 필수 필드가 존재하는지 확인한다."""
    required_fields = {
        "finding_id",
        "scan_id",
        "detector",
        "secret_type",
        "provider",
        "masked_value",
        "fingerprint",
        "file_path",
        "line_number",
        "detection_line",
        "context_before",
        "context_after",
        "source",
        "validation",
    }

    missing_fields = required_fields - finding.keys()

    if missing_fields:
        raise ValueError(f"정규화된 Finding에 필수 필드가 누락됐습니다: {sorted(missing_fields)}")

    leaked_raw_keys = RAW_SECRET_KEYS & finding.keys()

    if leaked_raw_keys:
        raise ValueError(f"정규화된 Finding에 원본 Secret 필드가 포함됐습니다: {sorted(leaked_raw_keys)}")

    if not isinstance(finding["line_number"], int):
        raise TypeError("line_number는 정수여야 합니다.")


def _first_non_empty(
    mapping: dict[str, Any],
    *keys: str,
) -> Any:
    """주어진 키 중 비어 있지 않은 첫 번째 값을 반환한다."""
    for key in keys:
        value = mapping.get(key)

        if value not in (None, "", [], {}):
            return value

    return None


def _normalize_detector(detector: object) -> str:
    """Detector 이름을 REGEX 또는 ENTROPY 형식으로 통일한다."""
    if detector is None:
        return "UNKNOWN"

    normalized = str(detector).upper()

    if "REGEX" in normalized or "PATTERN" in normalized:
        return "REGEX"

    if "ENTROPY" in normalized:
        return "ENTROPY"

    return normalized


def _normalize_line_number(line_number: object) -> int:
    """라인 번호를 정수로 변환한다."""
    if line_number is None:
        return 0

    try:
        return int(line_number)
    except (TypeError, ValueError):
        return 0


def _normalize_context_lines(value: object) -> list[str]:
    """문맥 데이터를 문자열 목록으로 변환한다."""
    if value is None:
        return []

    if isinstance(value, list):
        return [str(item) for item in value]

    return [str(value)]
