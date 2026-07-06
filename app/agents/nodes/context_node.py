from app.agents.state import AgentState


def context_node(state: AgentState) -> AgentState:
    """
    Context Analysis Node.

    역할:
    - raw_findings를 기반으로 파일명, 경로, 주변 문맥을 분석한다.
    - 1단계에서는 raw_findings가 비어 있으므로 빈 결과를 반환한다.
    """

    try:
        print("[Context Analysis Node] 실행")

        context_results = []

        for finding in state["raw_findings"]:
            context_results.append(
                {
                    "finding_id": finding.get("finding_id"),
                    "environment_hint": "unknown",
                    "file_type": "unknown",
                    "file_criticality": "unknown",
                    "context_keywords": [],
                    "context_summary": "1단계에서는 문맥 분석을 수행하지 않음",
                }
            )

        state["context_results"] = context_results

        return state

    except Exception as exc:
        state["errors"].append(f"Context Node Error: {str(exc)}")
        return state