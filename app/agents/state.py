from typing import Any, Dict, List, TypedDict


class AgentState(TypedDict):
    """
    LangGraph Node들이 공유하는 상태 객체.
    """

    target_path: str
    raw_findings: List[Dict[str, Any]]
    context_results: List[Dict[str, Any]]
    risk_results: List[Dict[str, Any]]
    policy_evidence: List[Dict[str, Any]]
    explanations: List[Dict[str, Any]]
    review_results: List[Dict[str, Any]]
    report_path: str
    errors: List[str]
