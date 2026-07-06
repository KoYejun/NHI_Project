from app.agents.state import AgentState


def review_node(state: AgentState) -> AgentState:
    """
    Human Review Node.

    역할:
    - Critical / High 항목을 관리자 검토 대상으로 분류한다.
    - 실제 폐기, 재발급, 권한 회수는 수행하지 않는다.
    - 검토 상태와 허용 가능한 후속 조치 후보만 생성한다.
    """

    try:
        print("[Human Review Node] 실행")

        review_results = []

        explanation_map = {item["finding_id"]: item for item in state["explanations"]}

        for risk in state["risk_results"]:
            finding_id = risk["finding_id"]
            explanation = explanation_map.get(finding_id, {})

            requires_review = risk["requires_human_review"]

            if requires_review:
                approval_status = "WAITING_HUMAN_REVIEW"
                decision = "PENDING"
                required_reviewer = "security_admin"
                allowed_actions = build_allowed_actions(risk)
                review_reason = explanation.get(
                    "human_review",
                    "Critical 또는 High 위험 항목으로 관리자 검토가 필요합니다.",
                )
            else:
                approval_status = "REVIEW_NOT_REQUIRED"
                decision = "NOT_REQUIRED"
                required_reviewer = ""
                allowed_actions = ["MONITOR", "VERIFY_FALSE_POSITIVE"]
                review_reason = "위험도가 Critical / High가 아니므로 즉시 관리자 검토 대상은 아닙니다."

            review_results.append(
                {
                    "finding_id": finding_id,
                    "approval_status": approval_status,
                    "decision": decision,
                    "required_reviewer": required_reviewer,
                    "allowed_actions": allowed_actions,
                    "review_reason": review_reason,
                    "reviewed_by": "",
                    "reviewed_at": "",
                    "reviewer_note": "",
                }
            )

        state["review_results"] = review_results

        return state

    except Exception as exc:
        state["errors"].append(f"Review Node Error: {str(exc)}")
        state["review_results"] = []
        return state


def build_allowed_actions(risk: dict) -> list[str]:
    risk_level = risk["risk_level"]
    secret_type = risk["secret_type"]

    actions = [
        "CHECK_ACCESS_LOG",
        "VERIFY_NHI_OWNER",
        "RECORD_REVIEW_RESULT",
    ]

    if risk_level == "Critical":
        actions.extend(
            [
                "ROTATE_SECRET",
                "REVOKE_SECRET_AFTER_APPROVAL",
                "MOVE_TO_SECRET_MANAGER",
            ]
        )

    if risk_level == "High":
        actions.extend(
            [
                "ROTATE_SECRET",
                "REDUCE_PERMISSION",
                "REQUEST_REAPPROVAL",
            ]
        )

    if secret_type == "AWS_ACCESS_KEY_ID":
        actions.append("CHECK_CLOUD_IAM_SCOPE")

    if secret_type == "GITHUB_TOKEN":
        actions.append("CHECK_REPOSITORY_SCOPE")

    if secret_type == "BEARER_TOKEN":
        actions.append("CHECK_API_ACCESS_LOG")

    return actions
