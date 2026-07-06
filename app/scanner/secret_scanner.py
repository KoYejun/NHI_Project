import re
from pathlib import Path
from typing import Any

from app.scanner.masking import mask_bearer_token, mask_secret

SUPPORTED_FILE_NAMES = {
    ".env",
}

SUPPORTED_EXTENSIONS = {
    ".py",
    ".js",
    ".java",
    ".go",
    ".yml",
    ".yaml",
    ".json",
    ".ini",
    ".md",
    ".txt",
    ".log",
}

MAX_FILE_SIZE_BYTES = 1024 * 1024


SECRET_PATTERNS = [
    {
        "secret_type": "AWS_ACCESS_KEY_ID",
        "matched_key": "AWS_ACCESS_KEY_ID",
        "detection_method": "regex",
        "regex": re.compile(r"\b(AKIA[0-9A-Z]{16})\b"),
        "secret_group": 1,
    },
    {
        "secret_type": "GITHUB_TOKEN",
        "matched_key": "GITHUB_TOKEN",
        "detection_method": "regex",
        "regex": re.compile(r"\b(ghp_[A-Za-z0-9_]{36,})\b"),
        "secret_group": 1,
    },
    {
        "secret_type": "SLACK_BOT_TOKEN",
        "matched_key": "SLACK_BOT_TOKEN",
        "detection_method": "regex",
        "regex": re.compile(r"\b(xoxb-[A-Za-z0-9-]{20,})\b"),
        "secret_group": 1,
    },
    {
        "secret_type": "BEARER_TOKEN",
        "matched_key": "Authorization",
        "detection_method": "regex",
        "regex": re.compile(
            r"\bAuthorization\s*:\s*Bearer\s+([A-Za-z0-9._\-+=/]{20,})\b",
            re.IGNORECASE,
        ),
        "secret_group": 1,
        "is_bearer": True,
    },
    {
        "secret_type": "GENERIC_CLIENT_SECRET",
        "matched_key": "client_secret",
        "detection_method": "regex",
        "regex": re.compile(
            r"\b(client[_-]?secret|api[_-]?key)\b\s*[:=]\s*[\"']?([A-Za-z0-9_\-./+=]{20,})[\"']?",
            re.IGNORECASE,
        ),
        "secret_group": 2,
        "key_group": 1,
    },
]


def scan_directory(target_path: str) -> list[dict[str, Any]]:
    """
    target_path 하위 파일을 스캔하여 Secret 후보를 반환한다.

    반환 결과에는 Secret 원문을 포함하지 않는다.
    masked_secret만 포함한다.
    """

    root_path = Path(target_path)

    if not root_path.exists():
        raise FileNotFoundError(f"Target path does not exist: {target_path}")

    if not root_path.is_dir():
        raise NotADirectoryError(f"Target path is not a directory: {target_path}")

    findings: list[dict[str, Any]] = []

    for file_path in sorted(root_path.rglob("*")):
        if not file_path.is_file():
            continue

        if not is_supported_file(file_path):
            continue

        if is_too_large(file_path):
            continue

        findings.extend(scan_file(file_path))

    findings.sort(
        key=lambda item: (
            item["file_path"],
            item["line_number"],
            item["secret_type"],
        )
    )

    for index, finding in enumerate(findings, start=1):
        finding["finding_id"] = f"finding_{index:03d}"

    return findings


def scan_file(file_path: Path) -> list[dict[str, Any]]:
    """
    단일 파일을 라인 단위로 스캔한다.
    """

    findings: list[dict[str, Any]] = []

    try:
        lines = file_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except UnicodeDecodeError:
        return findings

    for line_number, line in enumerate(lines, start=1):
        findings.extend(
            scan_line(
                file_path=file_path,
                line_number=line_number,
                line=line,
            )
        )

    return findings


def scan_line(file_path: Path, line_number: int, line: str) -> list[dict[str, Any]]:
    """
    한 줄에서 Secret 후보를 탐지한다.

    중복 탐지를 줄이기 위해 이미 탐지된 span과 겹치는 Generic Secret은 제외한다.
    """

    findings: list[dict[str, Any]] = []
    detected_spans: list[tuple[int, int]] = []

    for pattern in SECRET_PATTERNS:
        regex = pattern["regex"]

        for match in regex.finditer(line):
            secret_group = pattern["secret_group"]
            secret_value = match.group(secret_group)
            secret_span = match.span(secret_group)

            if has_overlap(secret_span, detected_spans):
                continue

            matched_key = pattern["matched_key"]

            if "key_group" in pattern:
                matched_key = match.group(pattern["key_group"])

            if pattern.get("is_bearer"):
                masked_secret = mask_bearer_token(secret_value)
            else:
                masked_secret = mask_secret(secret_value)

            findings.append(
                {
                    "finding_id": "",
                    "secret_type": pattern["secret_type"],
                    "masked_secret": masked_secret,
                    "file_path": normalize_path(file_path),
                    "line_number": line_number,
                    "matched_key": matched_key,
                    "detection_method": pattern["detection_method"],
                }
            )

            detected_spans.append(secret_span)

    return findings


def is_supported_file(file_path: Path) -> bool:
    """
    중간보고서 범위에 포함되는 파일만 스캔한다.
    """

    if file_path.name in SUPPORTED_FILE_NAMES:
        return True

    if file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
        return True

    return False


def is_too_large(file_path: Path) -> bool:
    """
    너무 큰 파일은 중간보고서 MVP에서 제외한다.
    """

    try:
        return file_path.stat().st_size > MAX_FILE_SIZE_BYTES
    except OSError:
        return True


def has_overlap(current_span: tuple[int, int], existing_spans: list[tuple[int, int]]) -> bool:
    """
    현재 탐지 위치가 이미 탐지된 Secret 위치와 겹치는지 확인한다.
    """

    current_start, current_end = current_span

    for existing_start, existing_end in existing_spans:
        if current_start < existing_end and existing_start < current_end:
            return True

    return False


def normalize_path(file_path: Path) -> str:
    """
    Windows에서도 리포트 경로를 / 기준으로 표시한다.
    """

    return file_path.as_posix()
