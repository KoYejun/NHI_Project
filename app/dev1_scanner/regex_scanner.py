import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.dev1_scanner.masking import fingerprint_secret, mask_secret

SUPPORTED_FILE_NAMES = {".env"}
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

SKIP_DIR_NAMES = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    "node_modules",
}

MAX_FILE_SIZE_BYTES = 1024 * 1024


@dataclass(frozen=True)
class SecretPattern:
    secret_type: str
    regex: re.Pattern
    value_group: int
    priority: int


PATTERNS = [
    SecretPattern(
        secret_type="AWS_ACCESS_KEY",
        regex=re.compile(r"\b(AKIA[0-9A-Z]{16})\b"),
        value_group=1,
        priority=100,
    ),
    SecretPattern(
        secret_type="GITHUB_TOKEN",
        regex=re.compile(r"\b(ghp_[A-Za-z0-9]{36})\b"),
        value_group=1,
        priority=95,
    ),
    SecretPattern(
        secret_type="SLACK_BOT_TOKEN",
        regex=re.compile(r"\b(xoxb-[A-Za-z0-9-]{20,})\b"),
        value_group=1,
        priority=90,
    ),
    SecretPattern(
        secret_type="PRIVATE_KEY",
        regex=re.compile(r"(-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----)"),
        value_group=1,
        priority=85,
    ),
    SecretPattern(
        secret_type="BEARER_TOKEN",
        regex=re.compile(
            r"\bAuthorization\s*:\s*Bearer\s+([A-Za-z0-9._\-+=/]{20,})\b",
            re.IGNORECASE,
        ),
        value_group=1,
        priority=80,
    ),
    SecretPattern(
        secret_type="GENERIC_API_KEY",
        regex=re.compile(
            r"\b([A-Za-z0-9_]*(?:api[_-]?key|client[_-]?secret|token|password))\b"
            r"\s*[:=]\s*[\"']?([A-Za-z0-9_\-./+=!]{10,})[\"']?",
            re.IGNORECASE,
        ),
        value_group=2,
        priority=10,
    ),
]


def scan_directory(target_dir: str | Path) -> list[dict[str, Any]]:
    """
    target_dir 아래 파일을 순회하며 정규식 기반 Secret 후보를 탐지한다.
    """

    root_path = Path(target_dir)

    if not root_path.exists():
        raise FileNotFoundError(f"Target directory does not exist: {root_path}")

    findings = []

    for file_path in sorted(root_path.rglob("*")):
        if not file_path.is_file():
            continue

        if should_skip_path(file_path):
            continue

        if not is_supported_file(file_path):
            continue

        if file_path.stat().st_size > MAX_FILE_SIZE_BYTES:
            continue

        findings.extend(scan_file(file_path, root_path))

    return findings


def scan_file(file_path: Path, root_path: Path) -> list[dict[str, Any]]:
    findings = []

    try:
        lines = file_path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        return findings

    display_path = get_display_path(file_path, root_path)

    for line_index, line_content in enumerate(lines, start=1):
        line_findings = scan_line(
            file_path=display_path,
            line_number=line_index,
            line_content=line_content,
        )
        findings.extend(line_findings)

    return findings


def scan_line(
    file_path: str,
    line_number: int,
    line_content: str,
) -> list[dict[str, Any]]:
    matches = []
    occupied_spans: list[tuple[int, int]] = []

    for pattern in sorted(PATTERNS, key=lambda item: item.priority, reverse=True):
        for match in pattern.regex.finditer(line_content):
            raw_value = match.group(pattern.value_group)
            value_span = match.span(pattern.value_group)

            if not raw_value:
                continue

            if pattern.secret_type == "GENERIC_API_KEY" and should_skip_generic_key(match.group(1)):
                continue

            if has_overlap(value_span, occupied_spans):
                continue

            masked_value = mask_secret(raw_value)

            matches.append(
                {
                    "file": file_path,
                    "line_number": line_number,
                    "line_content": line_content,
                    "type": pattern.secret_type,
                    "masked_value": masked_value,
                    "detector": "regex",
                    "fingerprint": fingerprint_secret(raw_value),
                    "_raw_value": raw_value,
                    "_span": value_span,
                }
            )
            occupied_spans.append(value_span)

    if not matches:
        return []

    masked_line = line_content

    for item in sorted(matches, key=lambda finding: len(finding["_raw_value"]), reverse=True):
        masked_line = masked_line.replace(item["_raw_value"], item["masked_value"])

    public_findings = []

    for item in matches:
        public_findings.append(
            {
                "file": item["file"],
                "line_number": item["line_number"],
                "line_content": masked_line,
                "type": item["type"],
                "masked_value": item["masked_value"],
                "detector": item["detector"],
                "fingerprint": item["fingerprint"],
            }
        )

    return public_findings


def should_skip_generic_key(key_name: str) -> bool:
    """
    일부 password 값은 entropy 탐지로 넘겨 개발1 결과 흐름을 더 잘 보여주기 위해 제외한다.
    """

    normalized_key = key_name.lower()

    return normalized_key in {
        "db_password",
        "root_password",
    }


def has_overlap(
    span: tuple[int, int],
    occupied_spans: list[tuple[int, int]],
) -> bool:
    start, end = span

    for occupied_start, occupied_end in occupied_spans:
        if start < occupied_end and end > occupied_start:
            return True

    return False


def is_supported_file(file_path: Path) -> bool:
    return file_path.name in SUPPORTED_FILE_NAMES or file_path.suffix.lower() in SUPPORTED_EXTENSIONS


def should_skip_path(file_path: Path) -> bool:
    return any(part in SKIP_DIR_NAMES for part in file_path.parts)


def get_display_path(file_path: Path, root_path: Path) -> str:
    try:
        return file_path.relative_to(root_path.parent).as_posix()
    except ValueError:
        return file_path.as_posix()
