from app.agents.state import AgentState
from app.policy.policy_retriever import retrieve_policy_evidence


def policy_node(state: AgentState) -> AgentState:
    """
    Policy Evidence Node.

    역할:
    - 위험도 분석 결과와 문맥 분석 결과를 기반으로 관련 정책 근거를 검색한다.
    - 현재는 keyword 기반 RAG-lite 방식으로 구현한다.
    """

    try:
        print("[Policy Evidence Node] 실행")

        policy_evidence = retrieve_policy_evidence(
            risk_results=state["risk_results"],
            context_results=state["context_results"],
            policy_dir="data/policies",
        )

        state["policy_evidence"] = policy_evidence

        return state

    except Exception as exc:
        state["errors"].append(f"Policy Node Error: {str(exc)}")
        state["policy_evidence"] = []
        return state
