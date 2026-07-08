import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from app.dev1_scanner import context_analyzer, entropy_scanner, regex_scanner, scoring

DEFAULT_OUTPUT_DIR = Path("reports")


def run_detection(target_path: str | Path) -> list[dict[str, Any]]:
    """
    정규식 탐지와 엔트로피 탐지를 실행한다.

    순서:
    1. regex_scanner 실행
    2. regex 결과의 fingerprint 집합 생성
    3. entropy_scanner 실행 시 중복 fingerprint 제외
    """

    regex_findings = regex_scanner.scan_directory(target_path)
    known_fingerprints = {finding["fingerprint"] for finding in regex_findings if finding.get("fingerprint")}

    entropy_findings = entropy_scanner.scan_directory(
        target_path,
        known_fingerprints=known_fingerprints,
    )

    findings = regex_findings + entropy_findings

    return sorted(
        findings,
        key=lambda item: (
            item.get("file", ""),
            item.get("line_number", 0),
            item.get("type", ""),
        ),
    )


def run_risk_analysis(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    탐지 결과에 대해 문맥 분석과 위험도 점수화를 수행한다.
    """

    fingerprint_counts = Counter(finding["fingerprint"] for finding in findings if finding.get("fingerprint"))

    risk_results = []

    for finding in findings:
        occurrence_count = fingerprint_counts.get(finding.get("fingerprint"), 1)

        context = context_analyzer.analyze(
            file_path=finding["file"],
            line_number=finding["line_number"],
        )

        risk = scoring.calculate_risk(
            secret_type=finding["type"],
            context=context,
            occurrence_count=occurrence_count,
        )

        risk_results.append(
            {
                "file": finding["file"],
                "line_number": finding["line_number"],
                "line_content": finding["line_content"],
                "type": finding["type"],
                "masked_value": finding["masked_value"],
                "detector": finding["detector"],
                "fingerprint": finding["fingerprint"],
                "occurrence_count": occurrence_count,
                "context": context,
                "risk": risk,
            }
        )

    return sorted(
        risk_results,
        key=lambda item: item["risk"]["score"],
        reverse=True,
    )


def run_full_scan(
    target_path: str | Path,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> dict[str, list[dict[str, Any]]]:
    """
    개발1 호환 전체 스캔을 실행하고,
    개발2 LangGraph에서 바로 사용할 수 있는 형식까지 함께 반환한다.
    """

    findings = run_detection(target_path)
    risk_results = run_risk_analysis(findings)

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    write_json(
        output_path / "raw_findings.json",
        strip_internal_fields(findings),
    )
    write_json(
        output_path / "risk_results.json",
        strip_internal_fields(risk_results),
    )

    return build_agent_outputs(risk_results)


def build_agent_outputs(
    risk_results: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    raw_findings = []
    context_results = []
    agent_risk_results = []

    for index, item in enumerate(risk_results, start=1):
        finding_id = f"finding_{index:03d}"
        context = item.get("context", {})
        risk = item.get("risk", {})

        raw_findings.append(
            {
                "finding_id": finding_id,
                "file_path": normalize_file_path(item.get("file", "")),
                "line_number": item.get("line_number", 0),
                "line_content": item.get("line_content", ""),
                "secret_type": normalize_secret_type(item.get("type", "UNKNOWN")),
                "masked_secret": item.get("masked_value", ""),
                "detector": item.get("detector", "unknown"),
                "occurrence_count": item.get("occurrence_count", 1),
            }
        )

        context_results.append(
            {
                "finding_id": finding_id,
                "file_path": normalize_file_path(item.get("file", "")),
                "file_type": context.get("file_type", "other"),
                "environment_hint": normalize_environment(context.get("environment", "unknown")),
                "file_criticality": infer_file_criticality(context.get("file_type", "other")),
                "context_keywords": context.get("keywords_found", []),
                "context_summary": build_context_summary(context),
            }
        )

        risk_level = risk.get("grade", "Low")

        agent_risk_results.append(
            {
                "finding_id": finding_id,
                "file_path": normalize_file_path(item.get("file", "")),
                "line_number": item.get("line_number", 0),
                "line_content": item.get("line_content", ""),
                "secret_type": normalize_secret_type(item.get("type", "UNKNOWN")),
                "masked_secret": item.get("masked_value", ""),
                "detector": item.get("detector", "unknown"),
                "occurrence_count": item.get("occurrence_count", 1),
                "risk_score": risk.get("score", 0),
                "risk_level": risk_level,
                "requires_human_review": risk_level in {"Critical", "High"},
                "score_detail": {
                    "type_risk": risk.get("type_risk", 0),
                    "exposure_risk": risk.get("exposure_risk", 0),
                    "base_score": risk.get("base_score", 0),
                    "context_bonus": risk.get("context_bonus", 0),
                    "file_criticality_bonus": risk.get("file_criticality_bonus", 0),
                    "frequency_bonus": risk.get("frequency_bonus", 0),
                },
            }
        )

    return {
        "raw_findings": raw_findings,
        "context_results": context_results,
        "risk_results": agent_risk_results,
    }


def normalize_secret_type(secret_type: str) -> str:
    mapping = {
        "AWS_ACCESS_KEY": "AWS_ACCESS_KEY_ID",
        "AWS_ACCESS_KEY_ID": "AWS_ACCESS_KEY_ID",
        "GITHUB_TOKEN": "GITHUB_TOKEN",
        "SLACK_BOT_TOKEN": "SLACK_BOT_TOKEN",
        "PRIVATE_KEY": "PRIVATE_KEY",
        "GENERIC_API_KEY": "GENERIC_API_KEY",
        "BEARER_TOKEN": "BEARER_TOKEN",
        "HIGH_ENTROPY_STRING": "HIGH_ENTROPY_STRING",
    }

    return mapping.get(secret_type, secret_type)


def normalize_environment(environment: str) -> str:
    mapping = {
        "prod": "production",
        "dev": "development",
        "test": "test",
        "unknown": "unknown",
    }

    return mapping.get(environment, environment)


def normalize_file_path(file_path: str) -> str:
    normalized = file_path.replace("\\", "/")

    if normalized.startswith("sample_project/"):
        return "data/" + normalized

    return normalized


def infer_file_criticality(file_type: str) -> str:
    if file_type in {"env", "config"}:
        return "high"

    if file_type in {"log", "code"}:
        return "medium"

    return "low"


def build_context_summary(context: dict[str, Any]) -> str:
    file_type = context.get("file_type", "other")
    environment = normalize_environment(context.get("environment", "unknown"))
    keywords = context.get("keywords_found", [])

    keyword_text = ", ".join(keywords) if keywords else "특이 키워드 없음"

    return (
        f"{file_type} 유형 파일에서 Secret 후보가 발견되었습니다. "
        f"환경 단서는 {environment}이며, 문맥 키워드는 {keyword_text}입니다."
    )


def strip_internal_fields(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    public_items = []

    for item in items:
        public_item = {key: value for key, value in item.items() if key != "fingerprint"}
        public_items.append(public_item)

    return public_items


def write_json(path: Path, data: list[dict[str, Any]]) -> None:
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def summarize_risk_levels(risk_results: list[dict[str, Any]]) -> dict[str, int]:
    summary = {
        "Critical": 0,
        "High": 0,
        "Medium": 0,
        "Low": 0,
    }

    for item in risk_results:
        grade = item.get("risk", {}).get("grade", "Low")
        summary[grade] = summary.get(grade, 0) + 1

    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Dev1 compatible secret scanner")
    parser.add_argument(
        "--target-path",
        default="data/sample_project",
        help="스캔 대상 폴더 경로",
    )
    args = parser.parse_args()

    findings = run_detection(args.target_path)
    risk_results = run_risk_analysis(findings)

    DEFAULT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    write_json(DEFAULT_OUTPUT_DIR / "raw_findings.json", strip_internal_fields(findings))
    write_json(DEFAULT_OUTPUT_DIR / "risk_results.json", strip_internal_fields(risk_results))

    summary = summarize_risk_levels(risk_results)

    print("\n=== Dev1 Compatible Scanner Result ===")
    print(f"Target Path: {args.target_path}")
    print(f"Raw Findings: {len(findings)}")
    print(f"Risk Results: {len(risk_results)}")
    print(f"Critical: {summary['Critical']}")
    print(f"High: {summary['High']}")
    print(f"Medium: {summary['Medium']}")
    print(f"Low: {summary['Low']}")
    print("Output: reports/raw_findings.json")
    print("Output: reports/risk_results.json")


if __name__ == "__main__":
    main()
