import json
from pathlib import Path

from app.agents.state import AgentState


def report_node(state: AgentState) -> AgentState:
    """
    Report Node.

    역할:
    - 최종 분석 결과를 JSON과 Markdown으로 저장한다.
    """

    try:
        print("[Report Node] 실행")

        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)

        result_path = reports_dir / "result.json"
        markdown_path = reports_dir / "report.md"

        final_result = build_final_result(state)

        result_path.write_text(
            json.dumps(final_result, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        markdown_report = build_markdown_report(final_result)
        markdown_path.write_text(markdown_report, encoding="utf-8")

        state["report_path"] = markdown_path.as_posix()

        return state

    except Exception as exc:
        state["errors"].append(f"Report Node Error: {str(exc)}")
        return state


def build_final_result(state: AgentState) -> dict:
    return {
        "target_path": state["target_path"],
        "summary": build_summary(state),
        "findings": build_detailed_findings(state),
        "errors": state["errors"],
    }


def build_summary(state: AgentState) -> dict:
    summary = {
        "total": len(state["risk_results"]),
        "Critical": 0,
        "High": 0,
        "Medium": 0,
        "Low": 0,
        "human_review_required": 0,
        "waiting_human_review": 0,
        "review_not_required": 0,
    }

    review_map = {item["finding_id"]: item for item in state["review_results"]}

    for risk in state["risk_results"]:
        risk_level = risk["risk_level"]
        finding_id = risk["finding_id"]

        summary[risk_level] = summary.get(risk_level, 0) + 1

        if risk["requires_human_review"]:
            summary["human_review_required"] += 1

        review_result = review_map.get(finding_id, {})
        approval_status = review_result.get("approval_status")

        if approval_status == "WAITING_HUMAN_REVIEW":
            summary["waiting_human_review"] += 1

        if approval_status == "REVIEW_NOT_REQUIRED":
            summary["review_not_required"] += 1

    return summary


def build_detailed_findings(state: AgentState) -> list[dict]:
    context_map = {item["finding_id"]: item for item in state["context_results"]}
    explanation_map = {item["finding_id"]: item for item in state["explanations"]}
    policy_map = {item["finding_id"]: item for item in state["policy_evidence"]}
    review_map = {item["finding_id"]: item for item in state["review_results"]}

    detailed_findings = []

    for risk in state["risk_results"]:
        finding_id = risk["finding_id"]

        detailed_findings.append(
            {
                "finding_id": finding_id,
                "secret_type": risk["secret_type"],
                "masked_secret": risk["masked_secret"],
                "file_path": risk["file_path"],
                "line_number": risk["line_number"],
                "line_content": risk.get("line_content", ""),
                "detector": risk.get("detector", "unknown"),
                "occurrence_count": risk.get("occurrence_count", 1),
                "risk_score": risk["risk_score"],
                "risk_level": risk["risk_level"],
                "score_detail": risk["score_detail"],
                "requires_human_review": risk["requires_human_review"],
                "context": context_map.get(finding_id, {}),
                "policy_evidence": policy_map.get(finding_id, {"matched_policies": []}),
                "agent_explanation": explanation_map.get(finding_id, {}),
                "review_status": review_map.get(finding_id, {}),
            }
        )

    return detailed_findings


def build_markdown_report(result: dict) -> str:
    summary = result["summary"]
    findings = result["findings"]

    lines = []

    lines.append("# NHI Secret 노출 탐지 리포트")
    lines.append("")
    lines.append("## 1. 요약")
    lines.append("")
    lines.append(f"- 분석 대상 경로: `{result['target_path']}`")
    lines.append(f"- 총 탐지 건수: `{summary['total']}`건")
    lines.append(f"- Critical: `{summary['Critical']}`건")
    lines.append(f"- High: `{summary['High']}`건")
    lines.append(f"- Medium: `{summary['Medium']}`건")
    lines.append(f"- Low: `{summary['Low']}`건")
    lines.append(f"- 관리자 검토 필요 항목: `{summary['human_review_required']}`건")
    lines.append(f"- 대기 중인 Human Review 항목: `{summary['waiting_human_review']}`건")
    lines.append("")

    lines.append("## 2. 상세 탐지 결과")
    lines.append("")

    for index, finding in enumerate(findings, start=1):
        explanation = finding["agent_explanation"]
        context = finding["context"]
        score_detail = finding["score_detail"]
        policy_evidence = finding["policy_evidence"]
        review_status = finding["review_status"]

        lines.append(f"### Finding {index}. {finding['risk_level']} / {finding['secret_type']}")
        lines.append("")
        lines.append(f"- Finding ID: `{finding['finding_id']}`")
        lines.append(f"- 파일 경로: `{finding['file_path']}`")
        lines.append(f"- 라인 번호: `{finding['line_number']}`")
        lines.append(f"- 탐지 방식: `{finding.get('detector', 'unknown')}`")
        lines.append(f"- 반복 노출 횟수: `{finding.get('occurrence_count', 1)}`")
        lines.append(f"- 마스킹 Secret: `{finding['masked_secret']}`")
        lines.append(f"- 위험 점수: `{finding['risk_score']}`")
        lines.append(f"- 위험 등급: `{finding['risk_level']}`")
        lines.append(f"- 관리자 검토 필요: `{finding['requires_human_review']}`")
        if finding.get("line_content"):
            lines.append("")
            lines.append("#### 탐지 라인")
            lines.append("")
            lines.append("```text")
            lines.append(finding["line_content"])
            lines.append("```")
            lines.append("")
        lines.append("")

        lines.append("#### 점수 산정 근거")
        lines.append("")
        lines.append(f"- TypeRisk: `{score_detail['type_risk']}`")
        lines.append(f"- ExposureRisk: `{score_detail['exposure_risk']}`")
        lines.append(f"- ContextBonus: `{score_detail['context_bonus']}`")
        lines.append(f"- FileCriticalityBonus: `{score_detail['file_criticality_bonus']}`")
        lines.append(f"- FrequencyBonus: `{score_detail['frequency_bonus']}`")
        lines.append("")

        lines.append("#### 문맥 분석")
        lines.append("")
        lines.append(f"- 파일 유형: `{context.get('file_type')}`")
        lines.append(f"- 환경 단서: `{context.get('environment_hint')}`")
        lines.append(f"- 파일 중요도: `{context.get('file_criticality')}`")
        lines.append(f"- 문맥 키워드: `{', '.join(context.get('context_keywords', []))}`")
        lines.append(f"- 문맥 요약: {context.get('context_summary')}")
        lines.append("")

        lines.append("#### 정책 근거")
        lines.append("")
        matched_policies = policy_evidence.get("matched_policies", [])

        for policy in matched_policies:
            lines.append(f"- `{policy['policy_id']}` {policy['title']}")
            lines.append(f"  - 관련도 점수: `{policy['relevance_score']}`")
            lines.append(f"  - 요약: {policy['summary']}")

        lines.append("")
        lines.append("#### Agent 분석")
        lines.append("")
        lines.append(f"- 탐지 요약: {explanation.get('summary')}")
        lines.append(f"- 위험 판단: {explanation.get('risk_reason')}")
        lines.append(f"- NHI 연결 가능성: {explanation.get('nhi_possibility')}")
        lines.append(f"- 가능한 영향: {explanation.get('possible_impact')}")
        lines.append(f"- 정책 근거 요약: {explanation.get('policy_basis')}")
        lines.append(f"- 대응 권고: {explanation.get('recommendation')}")
        lines.append(f"- 사람 검토: {explanation.get('human_review')}")
        lines.append("")

        lines.append("#### Human Review 상태")
        lines.append("")
        lines.append(f"- 승인 상태: `{review_status.get('approval_status')}`")
        lines.append(f"- 결정 상태: `{review_status.get('decision')}`")
        lines.append(f"- 필요 검토자: `{review_status.get('required_reviewer')}`")
        lines.append(f"- 검토 사유: {review_status.get('review_reason')}")
        lines.append(f"- 허용 가능한 후속 조치: `{', '.join(review_status.get('allowed_actions', []))}`")
        lines.append("")

    lines.append("## 3. 보안 설계 원칙")
    lines.append("")
    lines.append("- 본 리포트에는 Secret 원문을 저장하지 않는다.")
    lines.append("- 탐지 결과는 마스킹된 Secret만 포함한다.")
    lines.append("- Critical 또는 High 등급은 자동 조치하지 않고 관리자 검토 대상으로 분류한다.")
    lines.append("- 실제 Secret 유효성 검증, 실제 폐기, 실제 권한 회수는 수행하지 않는다.")
    lines.append("- Human Review 결정은 감사 로그로 기록한다.")
    lines.append("")

    lines.append("## 4. 현재 한계 및 다음 단계")
    lines.append("")
    lines.append("- 현재 Human Review는 로컬 JSON 상태 파일과 JSONL 감사 로그로 관리한다.")
    lines.append("- 실제 승인 시스템, IAM 권한 회수, Secret Manager API와는 연동하지 않는다.")
    lines.append("- 향후 조직 내 승인 워크플로, 티켓 시스템, 알림 시스템과 연동할 수 있다.")
    lines.append("")

    return "\n".join(lines)
