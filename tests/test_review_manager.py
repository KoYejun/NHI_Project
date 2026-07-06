from app.review.review_manager import (
    load_review_status,
    read_audit_logs,
    save_review_decision,
)


def test_save_review_decision_creates_status_and_audit_log(tmp_path):
    status_path = tmp_path / "review_status.json"
    audit_log_path = tmp_path / "audit_log.jsonl"

    record = save_review_decision(
        finding_id="finding_001",
        status="APPROVED_ROTATION",
        reviewer="security_admin",
        note="Secret rotation approved for test.",
        status_path=status_path,
        audit_log_path=audit_log_path,
    )

    assert record["finding_id"] == "finding_001"
    assert record["status"] == "APPROVED_ROTATION"
    assert record["reviewer"] == "security_admin"

    saved_status = load_review_status(status_path)
    assert saved_status["finding_001"]["status"] == "APPROVED_ROTATION"

    audit_logs = read_audit_logs(audit_log_path)
    assert len(audit_logs) == 1
    assert audit_logs[0]["event_type"] == "REVIEW_DECISION_UPDATED"
    assert audit_logs[0]["finding_id"] == "finding_001"
    assert audit_logs[0]["status"] == "APPROVED_ROTATION"
