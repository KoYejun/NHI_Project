import math
import re
from pathlib import Path
from typing import Any

from app.dev1_scanner.masking import fingerprint_secret, mask_secret
from app.dev1_scanner.regex_scanner import (
    MAX_FILE_SIZE_BYTES,
    is_supported_file,
    should_skip_path,
)

MIN_TOKEN_LENGTH = 12
ENTROPY_THRESHOLD = 3.5

ASSIGNMENT_VALUE_PATTERN = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*\s*[:=]\s*[\"']?([A-Za-z0-9_\-./+=!]{12,})[\"']?")

QUOTED_VALUE_PATTERN = re.compile(r"[\"']([A-Za-z0-9_\-./+=!]{12,})[\"']")


def scan_directory(
    target_dir: str | Path,
    known_fingerprints: set[str] | None = None,
) -> list[dict[str, Any]]:
    root_path = Path(target_dir)

    if not root_path.exists():
        raise FileNotFoundError(f"Target directory does not exist: {root_path}")

    known_fingerprints = known_fingerprints or set()
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

        findings.extend(scan_file(file_path, root_path, known_fingerprints))

    return findings


def scan_file(
    file_path: Path,
    root_path: Path,
    known_fingerprints: set[str],
) -> list[dict[str, Any]]:
    findings = []

    try:
        lines = file_path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        return findings

    display_path = get_display_path(file_path, root_path)

    for line_index, line_content in enumerate(lines, start=1):
        findings.extend(
            scan_line(
                file_path=display_path,
                line_number=line_index,
                line_content=line_content,
                known_fingerprints=known_fingerprints,
            )
        )

    return findings


def scan_line(
    file_path: str,
    line_number: int,
    line_content: str,
    known_fingerprints: set[str],
) -> list[dict[str, Any]]:
    candidates = extract_candidates(line_content)

    if not candidates:
        return []

    findings = []
    masked_line = line_content
    seen_fingerprints = set()

    for candidate in candidates:
        raw_value = candidate["value"]
        token_fingerprint = fingerprint_secret(raw_value)

        if token_fingerprint in known_fingerprints:
            continue

        if token_fingerprint in seen_fingerprints:
            continue

        if not looks_like_high_entropy_secret(raw_value):
            continue

        masked_value = mask_secret(raw_value)
        masked_line = masked_line.replace(raw_value, masked_value)
        seen_fingerprints.add(token_fingerprint)

        findings.append(
            {
                "file": file_path,
                "line_number": line_number,
                "line_content": masked_line,
                "type": "HIGH_ENTROPY_STRING",
                "masked_value": masked_value,
                "detector": "entropy",
                "fingerprint": token_fingerprint,
            }
        )

    return findings


def extract_candidates(line_content: str) -> list[dict[str, Any]]:
    candidates = []
    occupied_spans: list[tuple[int, int]] = []

    for pattern in [ASSIGNMENT_VALUE_PATTERN, QUOTED_VALUE_PATTERN]:
        for match in pattern.finditer(line_content):
            raw_value = match.group(1)
            span = match.span(1)

            if has_overlap(span, occupied_spans):
                continue

            candidates.append(
                {
                    "value": raw_value,
                    "span": span,
                }
            )
            occupied_spans.append(span)

    return candidates


def looks_like_high_entropy_secret(value: str) -> bool:
    if len(value) < MIN_TOKEN_LENGTH:
        return False

    if not has_letter_and_digit(value):
        return False

    if is_obvious_non_secret(value):
        return False

    return shannon_entropy(value) >= ENTROPY_THRESHOLD


def has_letter_and_digit(value: str) -> bool:
    has_letter = any(character.isalpha() for character in value)
    has_digit = any(character.isdigit() for character in value)

    return has_letter and has_digit


def is_obvious_non_secret(value: str) -> bool:
    lowered = value.lower()

    if lowered.startswith(("http://", "https://")):
        return True

    if "example.com" in lowered:
        return True

    return False


def shannon_entropy(value: str) -> float:
    if not value:
        return 0.0

    frequency = {}

    for character in value:
        frequency[character] = frequency.get(character, 0) + 1

    entropy = 0.0
    length = len(value)

    for count in frequency.values():
        probability = count / length
        entropy -= probability * math.log2(probability)

    return entropy


def has_overlap(
    span: tuple[int, int],
    occupied_spans: list[tuple[int, int]],
) -> bool:
    start, end = span

    for occupied_start, occupied_end in occupied_spans:
        if start < occupied_end and end > occupied_start:
            return True

    return False


def get_display_path(file_path: Path, root_path: Path) -> str:
    try:
        return file_path.relative_to(root_path.parent).as_posix()
    except ValueError:
        return file_path.as_posix()
