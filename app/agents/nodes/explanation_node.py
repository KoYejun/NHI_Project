from app.agents.state import AgentState


def explanation_node(state: AgentState) -> AgentState:
    """
    Explanation Node.

    역할:
    - 위험도 분석 결과를 사람이 이해할 수 있는 관리자용 설명으로 변환한다.
    - 1단계에서는 risk_results가 비어 있으므로 빈 결과를 반환한다.
    """

    try:
        print("[Explanation Node] 실행")

        explanations = []

        for risk in state["risk_results"]:
            explanations.append(
                {
                    "finding_id": risk.get("finding_id"),
                    "summary": "1단계에서는 Agent 설명을 생성하지 않음",
                    "risk_reason": "1단계에서는 위험 판단을 수행하지 않음",
                    "nhi_possibility": "1단계에서는 NHI 연결 가능성을 분석하지 않음",
                    "possible_impact": "1단계에서는 영향을 분석하지 않음",
                    "recommendation": "1단계에서는 대응 권고를 생성하지 않음",
                    "human_review": "1단계에서는 관리자 검토 여부를 판단하지 않음",
                }
            )

        state["explanations"] = explanations

        return state

    except Exception as exc:
        state["errors"].append(f"Explanation Node Error: {str(exc)}")
        return state