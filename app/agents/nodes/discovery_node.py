from app.agents.state import AgentState
from app.scanner.secret_scanner import scan_directory


def discovery_node(state: AgentState) -> AgentState:
    """
    Discovery Node.

    역할:
    - target_path 하위 파일을 스캔한다.
    - Secret 후보를 탐지한다.
    - 탐지 결과를 raw_findings에 저장한다.

    보안 원칙:
    - Secret 원문은 State에 저장하지 않는다.
    - masked_secret만 다음 Node로 전달한다.
    """

    try:
        print("[Discovery Node] 실행")

        target_path = state["target_path"]
        raw_findings = scan_directory(target_path)

        state["raw_findings"] = raw_findings

        return state

    except Exception as exc:
        state["errors"].append(f"Discovery Node Error: {str(exc)}")
        state["raw_findings"] = []
        return state
