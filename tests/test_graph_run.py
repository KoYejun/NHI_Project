import json
from pathlib import Path

from app.agents.graph import build_graph

RAW_SECRETS = [
    "AKIA1234567890ABCDEF",
    "ghp_abcdefghijklmnopqrstuvwxyz1234567890",
    "sample_client_secret_abcdefghijklmnopqrstuvwxyz",
    "sampleBearerToken1234567890abcdef",
]


def create_sample_project(base_path: Path) -> Path:
    sample_project = base_path / "data" / "sample_project"
    sample_project.mkdir(parents=True)

    (sample_project / ".env").write_text(
        "\n".join(
            [
                "APP_ENV=production",
                "DB_HOST=prod-db.internal",
                "AWS_ACCESS_KEY_ID=AKIA1234567890ABCDEF",
                'DATABASE_PASSWORD="sample-password"',
            ]
        ),
        encoding="utf-8",
    )

    (sample_project / "app.py").write_text(
        "\n".join(
            [
                'API_URL = "https://api.example.com"',
                "",
                "# 테스트용 가짜 토큰",
                'GITHUB_TOKEN = "ghp_abcdefghijklmnopqrstuvwxyz1234567890"',
            ]
        ),
        encoding="utf-8",
    )

    (sample_project / "config.yml").write_text(
        "\n".join(
            [
                "app:",
                "  name: sample-service",
                "  environment: dev",
                "",
                "oauth:",
                "  client_id: sample-client-id",
                "  client_secret: sample_client_secret_abcdefghijklmnopqrstuvwxyz",
            ]
        ),
        encoding="utf-8",
    )

    (sample_project / "server.log").write_text(
        "\n".join(
            [
                "2026-07-05 10:22:10 INFO Server started",
                "2026-07-05 10:22:11 DEBUG Authorization: Bearer sampleBearerToken1234567890abcdef",
                "2026-07-05 10:22:12 INFO Request completed",
            ]
        ),
        encoding="utf-8",
    )

    return sample_project


def test_graph_run_creates_json_and_markdown_reports(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    create_sample_project(tmp_path)

    graph = build_graph()

    initial_state = {
        "target_path": "data/sample_project",
        "raw_findings": [],
        "context_results": [],
        "risk_results": [],
        "explanations": [],
        "report_path": "",
        "errors": [],
    }

    final_state = graph.invoke(initial_state)

    assert final_state["errors"] == []
    assert len(final_state["raw_findings"]) == 4
    assert len(final_state["context_results"]) == 4
    assert len(final_state["risk_results"]) == 4
    assert len(final_state["explanations"]) == 4
    assert final_state["report_path"] == "reports/report.md"

    assert Path("reports/report.md").exists()
    assert Path("reports/result.json").exists()


def test_report_files_do_not_include_raw_secret_values(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    create_sample_project(tmp_path)

    graph = build_graph()

    initial_state = {
        "target_path": "data/sample_project",
        "raw_findings": [],
        "context_results": [],
        "risk_results": [],
        "explanations": [],
        "report_path": "",
        "errors": [],
    }

    graph.invoke(initial_state)

    report_text = Path("reports/report.md").read_text(encoding="utf-8")
    result_text = Path("reports/result.json").read_text(encoding="utf-8")

    for raw_secret in RAW_SECRETS:
        assert raw_secret not in report_text
        assert raw_secret not in result_text

    assert "AKIA************CDEF" in report_text
    assert "masked_secret" in result_text


def test_result_json_contains_expected_summary(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    create_sample_project(tmp_path)

    graph = build_graph()

    initial_state = {
        "target_path": "data/sample_project",
        "raw_findings": [],
        "context_results": [],
        "risk_results": [],
        "explanations": [],
        "report_path": "",
        "errors": [],
    }

    graph.invoke(initial_state)

    result = json.loads(Path("reports/result.json").read_text(encoding="utf-8"))
    summary = result["summary"]

    assert summary["total"] == 4
    assert summary["Critical"] == 1
    assert summary["High"] == 1
    assert summary["Medium"] == 2
    assert summary["Low"] == 0
    assert summary["human_review_required"] == 2
