import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REVIEW_STATUS_PATH = Path("reports/review_status.json")
AUDIT_LOG_PATH = Path("reports/audit_log.jsonl")


VALID_REVIEW_STATUSES = {
    "WAITING_HUMAN_REVIEW",
    "APPROVED_ROTATION",
    "FALSE_POSITIVE",
    "ACCEPTED_RISK",
    "RESOLVED",
    "REVIEW_NOT_REQUIRED",
}


def get_current_utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_review_status(
    status_path: Path = REVIEW_STATUS_PATH,
) -> dict[str, dict[str, Any]]:
    """
    저장된 Human Review 상태를 불러온다.

    파일이 없으면 빈 dict를 반환한다.
    """

    if not status_path.exists():
        return {}

    try:
        data = json.loads(status_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}

    if not isinstance(data, dict):
        return {}

    return data


def save_review_decision(
    finding_id: str,
    status: str,
    reviewer: str,
    note: str,
    status_path: Path = REVIEW_STATUS_PATH,
    audit_log_path: Path = AUDIT_LOG_PATH,
) -> dict[str, Any]:
    """
    특정 Finding의 Human Review 상태를 저장하고 감사 로그를 남긴다.

    실제 Secret 폐기, 권한 회수, 외부 API 호출은 수행하지 않는다.
    """

    if status not in VALID_REVIEW_STATUSES:
        raise ValueError(f"Invalid review status: {status}")

    status_path.parent.mkdir(parents=True, exist_ok=True)

    review_status = load_review_status(status_path)
    reviewed_at = get_current_utc_timestamp()

    record = {
        "finding_id": finding_id,
        "status": status,
        "reviewer": reviewer.strip() or "unknown_reviewer",
        "note": note.strip(),
        "reviewed_at": reviewed_at,
    }

    review_status[finding_id] = record

    status_path.write_text(
        json.dumps(review_status, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    append_audit_log(
        {
            "event_type": "REVIEW_DECISION_UPDATED",
            "finding_id": finding_id,
            "status": status,
            "reviewer": record["reviewer"],
            "note": record["note"],
        },
        audit_log_path=audit_log_path,
    )

    return record


def append_audit_log(
    event: dict[str, Any],
    audit_log_path: Path = AUDIT_LOG_PATH,
) -> None:
    """
    감사 로그를 JSONL 형식으로 append한다.
    """

    audit_log_path.parent.mkdir(parents=True, exist_ok=True)

    event_with_time = {
        "event_time": get_current_utc_timestamp(),
        **event,
    }

    with audit_log_path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(event_with_time, ensure_ascii=False) + "\n")


def read_audit_logs(
    audit_log_path: Path = AUDIT_LOG_PATH,
) -> list[dict[str, Any]]:
    """
    JSONL 감사 로그를 읽는다.
    """

    if not audit_log_path.exists():
        return []

    logs = []

    for line in audit_log_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue

        try:
            logs.append(json.loads(line))
        except json.JSONDecodeError:
            continue

    return logs


def get_effective_review_status(
    finding: dict[str, Any],
    saved_status_map: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """
    result.json의 기본 review_status와
    대시보드에서 저장한 review_status.json 값을 합쳐 최종 상태를 만든다.
    """

    finding_id = finding.get("finding_id")
    base_status = finding.get("review_status", {})
    saved_status = saved_status_map.get(finding_id)

    if not saved_status:
        return {
            **base_status,
            "current_status": base_status.get("approval_status", "UNKNOWN"),
            "reviewer": "",
            "reviewed_at": "",
            "reviewer_note": "",
            "source": "agent_result",
        }

    return {
        **base_status,
        "current_status": saved_status.get(
            "status",
            base_status.get("approval_status", "UNKNOWN"),
        ),
        "reviewer": saved_status.get("reviewer", ""),
        "reviewed_at": saved_status.get("reviewed_at", ""),
        "reviewer_note": saved_status.get("note", ""),
        "source": "manual_review",
    }
