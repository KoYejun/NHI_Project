from app.agents.state import AgentState


def discovery_node(state: AgentState) -> AgentState:
    """
    Discovery Node.

    역할:
    - 1번 담당자의 Secret Scanner를 호출하는 Node.
    - 1단계에서는 실제 Scanner를 호출하지 않고 빈 결과를 반환한다.
    - 2단계에서 mock finding을 넣고, 3단계에서 실제 Scanner와 연동한다.
    """

    try:
        print("[Discovery Node] 실행")

        # 1단계에서는 아직 실제 Secret 탐지를 하지 않는다.
        state["raw_findings"] = []

        return state

    except Exception as exc:
        state["errors"].append(f"Discovery Node Error: {str(exc)}")
        return state