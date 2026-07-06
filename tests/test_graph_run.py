import json
from pathlib import Path

from app.agents.graph import build_graph
from tests.sample_data_factory import RAW_SECRETS, create_sample_project


def build_initial_state() -> dict:
    return {
        "target_path": "data/sample_project",
        "raw_findings": [],
        "context_results": [],
        "risk_results": [],
        "policy_evidence": [],
        "explanations": [],
        "review_results": [],
        "report_path": "",
        "errors": [],
    }


def test_graph_run_creates_json_and_markdown_reports(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    create_sample_project(tmp_path, "data/sample_project")

    graph = build_graph()
    final_state = graph.invoke(build_initial_state())

    assert final_state["errors"] == []
    assert len(final_state["raw_findings"]) == 4
    assert len(final_state["context_results"]) == 4
    assert len(final_state["risk_results"]) == 4
    assert len(final_state["policy_evidence"]) == 4
    assert len(final_state["explanations"]) == 4
    assert len(final_state["review_results"]) == 4
    assert final_state["report_path"] == "reports/report.md"

    assert Path("reports/report.md").exists()
    assert Path("reports/result.json").exists()


def test_report_files_do_not_include_raw_secret_values(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    create_sample_project(tmp_path, "data/sample_project")

    graph = build_graph()
    graph.invoke(build_initial_state())

    report_text = Path("reports/report.md").read_text(encoding="utf-8")
    result_text = Path("reports/result.json").read_text(encoding="utf-8")

    for raw_secret in RAW_SECRETS:
        assert raw_secret not in report_text
        assert raw_secret not in result_text

    assert "AKIA************CDEF" in report_text
    assert "masked_secret" in result_text


def test_result_json_contains_expected_summary(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    create_sample_project(tmp_path, "data/sample_project")

    graph = build_graph()
    graph.invoke(build_initial_state())

    result = json.loads(Path("reports/result.json").read_text(encoding="utf-8"))
    summary = result["summary"]

    assert summary["total"] == 4
    assert summary["Critical"] == 1
    assert summary["High"] == 1
    assert summary["Medium"] == 2
    assert summary["Low"] == 0
    assert summary["human_review_required"] == 2
    assert summary["waiting_human_review"] == 2
    assert summary["review_not_required"] == 2


def test_result_json_contains_policy_evidence(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    create_sample_project(tmp_path, "data/sample_project")

    graph = build_graph()
    graph.invoke(build_initial_state())

    result = json.loads(Path("reports/result.json").read_text(encoding="utf-8"))

    for finding in result["findings"]:
        assert "policy_evidence" in finding
        assert "matched_policies" in finding["policy_evidence"]
        assert len(finding["policy_evidence"]["matched_policies"]) >= 1


def test_result_json_contains_review_status(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    create_sample_project(tmp_path, "data/sample_project")

    graph = build_graph()
    graph.invoke(build_initial_state())

    result = json.loads(Path("reports/result.json").read_text(encoding="utf-8"))

    review_statuses = {
        finding["finding_id"]: finding["review_status"]["approval_status"] for finding in result["findings"]
    }

    assert review_statuses["finding_001"] == "WAITING_HUMAN_REVIEW"
    assert review_statuses["finding_002"] == "REVIEW_NOT_REQUIRED"
    assert review_statuses["finding_003"] == "WAITING_HUMAN_REVIEW"
    assert review_statuses["finding_004"] == "REVIEW_NOT_REQUIRED"
