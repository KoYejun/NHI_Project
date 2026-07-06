from app.agents.state import AgentState


def explanation_node(state: AgentState) -> AgentState:
    """
    Explanation Node.

    역할:
    - 위험도 분석 결과를 관리자용 설명으로 변환한다.
    - LLM API 없이 규칙 기반 템플릿으로 생성한다.
    - 설명에는 탐지 요약, 위험 판단, NHI 연결 가능성, 영향, 대응 권고, 사람 검토를 포함한다.
    """

    try:
        print("[Explanation Node] 실행")

        explanations = []

        context_map = {item["finding_id"]: item for item in state["context_results"]}

        for risk in state["risk_results"]:
            finding_id = risk["finding_id"]
            context = context_map.get(finding_id, {})

            explanation = {
                "finding_id": finding_id,
                "summary": build_summary(risk),
                "risk_reason": build_risk_reason(risk, context),
                "nhi_possibility": build_nhi_possibility(risk),
                "possible_impact": build_possible_impact(risk),
                "recommendation": build_recommendation(risk),
                "human_review": build_human_review_message(risk),
            }

            explanations.append(explanation)

        state["explanations"] = explanations

        return state

    except Exception as exc:
        state["errors"].append(f"Explanation Node Error: {str(exc)}")
        return state


def build_summary(risk: dict) -> str:
    return (
        f"{risk['file_path']} 파일의 {risk['line_number']}번째 줄에서 "
        f"{risk['secret_type']} 유형의 Secret 후보가 발견되었습니다."
    )


def build_risk_reason(risk: dict, context: dict) -> str:
    reasons = []

    risk_level = risk["risk_level"]
    risk_score = risk["risk_score"]
    file_path = risk["file_path"]
    environment_hint = context.get("environment_hint", "unknown")
    file_criticality = context.get("file_criticality", "unknown")

    reasons.append(f"위험 점수는 {risk_score}점이며 위험 등급은 {risk_level}입니다.")

    if file_path.endswith(".env"):
        reasons.append(".env 파일은 애플리케이션 실행 환경의 민감 설정을 포함하는 경우가 많아 위험도가 높습니다.")

    if file_path.endswith((".yml", ".yaml", ".json", ".ini")):
        reasons.append("설정 파일은 인증정보, 외부 연동 정보, DB 접속 정보가 포함될 수 있어 주의가 필요합니다.")

    if file_path.endswith(".log"):
        reasons.append("로그 파일에 인증 헤더나 토큰이 남으면 운영 중 2차 노출 경로가 될 수 있습니다.")

    if environment_hint == "production":
        reasons.append("문맥상 production 환경으로 추정되어 실제 운영 Secret일 가능성이 있습니다.")

    if file_criticality == "high":
        reasons.append("파일 중요도가 high로 분류되어 우선 검토가 필요합니다.")

    return " ".join(reasons)


def build_nhi_possibility(risk: dict) -> str:
    secret_type = risk["secret_type"]

    if secret_type == "AWS_ACCESS_KEY_ID":
        return (
            "AWS Access Key는 서버 애플리케이션, 배포 자동화, CI/CD, 서비스 계정 등 "
            "Non-Human Identity 인증수단과 연결될 수 있습니다."
        )

    if secret_type == "GITHUB_TOKEN":
        return "GitHub Token은 저장소 접근, Actions 워크플로, 자동화 봇 계정과 연결될 수 있습니다."

    if secret_type == "GENERIC_CLIENT_SECRET":
        return "Client Secret은 OAuth 기반 애플리케이션 또는 외부 API 연동용 NHI 인증정보일 수 있습니다."

    if secret_type == "BEARER_TOKEN":
        return "Bearer Token은 API 호출 권한을 가진 자동화 프로세스나 서비스 계정 인증정보일 수 있습니다."

    return "해당 Secret은 자동화 계정 또는 서비스 계정의 인증정보로 사용될 가능성이 있습니다."


def build_possible_impact(risk: dict) -> str:
    secret_type = risk["secret_type"]

    if secret_type == "AWS_ACCESS_KEY_ID":
        return (
            "Key가 유효하다면 클라우드 리소스 조회, 데이터 접근, 배포 파이프라인 조작, "
            "권한 상승 시도로 이어질 수 있습니다."
        )

    if secret_type == "GITHUB_TOKEN":
        return "Token이 유효하다면 소스코드 조회, 저장소 설정 변경, CI/CD 워크플로 악용 위험이 있습니다."

    if secret_type == "GENERIC_CLIENT_SECRET":
        return "Client Secret이 유효하다면 외부 API 인증 우회, 애플리케이션 권한 오남용으로 이어질 수 있습니다."

    if secret_type == "BEARER_TOKEN":
        return "Bearer Token이 유효하다면 API 요청 위조, 사용자 또는 서비스 권한 남용 가능성이 있습니다."

    return "Secret의 권한 범위에 따라 내부 시스템, 데이터, API 접근 위험이 발생할 수 있습니다."


def build_recommendation(risk: dict) -> str:
    risk_level = risk["risk_level"]

    if risk_level == "Critical":
        return (
            "즉시 Secret 폐기 및 재발급을 검토하고, 연결된 NHI 권한 범위와 최근 접근 로그를 점검해야 합니다. "
            "이후 Secret Manager 이전과 pre-commit Secret Scan 적용을 권고합니다."
        )

    if risk_level == "High":
        return (
            "빠른 담당자 검토가 필요합니다. Secret 재발급, 권한 축소, 접근 로그 점검, "
            "저장소 히스토리 확인을 권고합니다."
        )

    if risk_level == "Medium":
        return (
            "담당자 확인을 통해 실제 사용 여부와 오탐 여부를 검토해야 합니다. "
            "필요 시 Secret Manager 이전과 로그 마스킹 정책을 적용합니다."
        )

    return "오탐 가능성을 고려해 모니터링 대상으로 분류하고, 동일 패턴 반복 노출 여부를 확인합니다."


def build_human_review_message(risk: dict) -> str:
    if risk["requires_human_review"]:
        return "관리자 검토가 필요합니다. 자동 폐기나 권한 회수는 수행하지 않고 Human Review 대상으로 분류합니다."

    return "즉시 관리자 승인은 필수는 아니지만, 담당자 확인 및 검토 이력 기록을 권고합니다."
