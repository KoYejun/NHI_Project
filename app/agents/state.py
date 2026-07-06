from typing import Any, Dict, List, TypedDict


class AgentState(TypedDict):
    """
    LangGraph Node들이 공유하는 상태 객체.

    target_path:
        분석 대상 폴더 경로

    raw_findings:
        Secret 탐지 결과.
        1번 담당자의 Scanner 결과가 들어오는 영역.

    context_results:
        파일명, 경로, 주변 문맥 분석 결과.

    risk_results:
        위험 점수와 위험 등급 계산 결과.

    explanations:
        Agent가 생성한 관리자용 설명문.

    report_path:
        최종 Markdown 리포트 경로.

    errors:
        Node 실행 중 발생한 에러 목록.
    """

    target_path: str
    raw_findings: List[Dict[str, Any]]
    context_results: List[Dict[str, Any]]
    risk_results: List[Dict[str, Any]]
    explanations: List[Dict[str, Any]]
    report_path: str
    errors: List[str]