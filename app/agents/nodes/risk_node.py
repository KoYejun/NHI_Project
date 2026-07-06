from app.agents.state import AgentState


def risk_node(state: AgentState) -> AgentState:
    """
    Risk Scoring Node.

    역할:
    - context_results와 raw_findings를 기반으로 위험 점수와 등급을 계산한다.
    - 1단계에서는 분석 대상이 없으므로 빈 결과를 반환한다.
    """

    try:
        print("[Risk Scoring Node] 실행")

        risk_results = []

        for finding in state["raw_findings"]:
            risk_results.append(
                {
                    "finding_id": finding.get("finding_id"),
                    "secret_type": finding.get("secret_type"),
                    "masked_secret": finding.get("masked_secret"),
                    "file_path": finding.get("file_path"),
                    "line_number": finding.get("line_number"),
                    "risk_score": 0,
                    "risk_level": "Low",
                    "requires_human_review": False,
                }
            )

        state["risk_results"] = risk_results

        return state

    except Exception as exc:
        state["errors"].append(f"Risk Node Error: {str(exc)}")
        return state