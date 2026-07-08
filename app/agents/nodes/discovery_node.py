from app.agents.state import AgentState
from app.dev1_scanner.run_scan import run_full_scan


def discovery_node(state: AgentState) -> AgentState:
    """
    Discovery Node.

    개발1 호환 Scanner Engine을 실행해
    raw_findings, context_results, risk_results를 한 번에 생성한다.
    """

    try:
        print("[Discovery Node] 개발1 호환 Scanner Engine 실행")

        target_path = state["target_path"]

        scan_result = run_full_scan(target_path)

        state["raw_findings"] = scan_result["raw_findings"]
        state["context_results"] = scan_result["context_results"]
        state["risk_results"] = scan_result["risk_results"]

        return state

    except Exception as exc:
        state["errors"].append(f"Discovery Node Error: {str(exc)}")
        state["raw_findings"] = []
        state["context_results"] = []
        state["risk_results"] = []
        return state
