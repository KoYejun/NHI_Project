from pathlib import Path

from app.agents.state import AgentState


def report_node(state: AgentState) -> AgentState:
    """
    Report Node.

    역할:
    - 최종 분석 결과를 리포트 파일로 저장한다.
    - 1단계에서는 Workflow 실행 확인용 Markdown 리포트만 생성한다.
    """

    try:
        print("[Report Node] 실행")

        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)

        report_path = reports_dir / "report.md"

        report_text = build_stage1_report(state)

        report_path.write_text(report_text, encoding="utf-8")

        state["report_path"] = str(report_path)

        return state

    except Exception as exc:
        state["errors"].append(f"Report Node Error: {str(exc)}")
        return state


def build_stage1_report(state: AgentState) -> str:
    """
    1단계용 기본 Markdown 리포트.
    """

    return f"""# NHI Secret 노출 탐지 리포트

## 1. 현재 단계

1단계: LangGraph Workflow 실행 뼈대 구현

## 2. 실행 상태

- 분석 대상 경로: `{state["target_path"]}`
- Secret 탐지 결과 수: `{len(state["raw_findings"])}`
- 문맥 분석 결과 수: `{len(state["context_results"])}`
- 위험도 분석 결과 수: `{len(state["risk_results"])}`
- Agent 설명 결과 수: `{len(state["explanations"])}`
- 에러 수: `{len(state["errors"])}`

## 3. 현재 한계

- 아직 실제 Secret Scanner는 연동하지 않음
- 아직 문맥 분석과 위험도 계산은 수행하지 않음
- 아직 Agent 설명은 생성하지 않음

## 4. 다음 단계

2단계에서 mock Secret 탐지 결과를 넣고,
Explanation Node와 Report Node가 실제 형태의 결과를 생성하도록 확장한다.
"""