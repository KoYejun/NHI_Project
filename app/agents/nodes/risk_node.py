from app.agents.state import AgentState


def risk_node(state: AgentState) -> AgentState:
    """
    Risk Scoring Node.

    역할:
    - Secret 유형, 노출 위치, 문맥, 파일 중요도를 바탕으로 위험 점수를 계산한다.
    - 중간보고서용 산식:
      SecretRisk = TypeRisk × ExposureRisk
                 + ContextBonus
                 + FileCriticalityBonus
                 + FrequencyBonus
    """

    try:
        print("[Risk Scoring Node] 실행")

        risk_results = []

        context_map = {item["finding_id"]: item for item in state["context_results"]}

        frequency_map = build_frequency_map(state["raw_findings"])

        for finding in state["raw_findings"]:
            finding_id = finding["finding_id"]
            context = context_map.get(finding_id, {})

            type_risk = get_type_risk(finding["secret_type"])
            exposure_risk = get_exposure_risk(finding["file_path"])
            context_bonus = get_context_bonus(context)
            file_bonus = get_file_criticality_bonus(context)
            frequency_bonus = get_frequency_bonus(
                finding=finding,
                frequency_map=frequency_map,
            )

            risk_score = type_risk * exposure_risk + context_bonus + file_bonus + frequency_bonus

            risk_level = get_risk_level(risk_score)

            risk_results.append(
                {
                    "finding_id": finding_id,
                    "secret_type": finding["secret_type"],
                    "masked_secret": finding["masked_secret"],
                    "file_path": finding["file_path"],
                    "line_number": finding["line_number"],
                    "risk_score": risk_score,
                    "risk_level": risk_level,
                    "score_detail": {
                        "type_risk": type_risk,
                        "exposure_risk": exposure_risk,
                        "context_bonus": context_bonus,
                        "file_criticality_bonus": file_bonus,
                        "frequency_bonus": frequency_bonus,
                    },
                    "requires_human_review": risk_level in ["Critical", "High"],
                }
            )

        state["risk_results"] = risk_results

        return state

    except Exception as exc:
        state["errors"].append(f"Risk Node Error: {str(exc)}")
        return state


def get_type_risk(secret_type: str) -> int:
    type_risk_table = {
        "AWS_ACCESS_KEY_ID": 10,
        "PRIVATE_KEY": 10,
        "GITHUB_TOKEN": 8,
        "SLACK_BOT_TOKEN": 8,
        "BEARER_TOKEN": 7,
        "GENERIC_CLIENT_SECRET": 7,
        "GENERIC_API_KEY": 6,
    }

    return type_risk_table.get(secret_type, 5)


def get_exposure_risk(file_path: str) -> int:
    lowered_path = file_path.lower()

    if lowered_path.endswith(".env"):
        return 8

    if lowered_path.endswith((".yml", ".yaml", ".json", ".ini")):
        return 8

    if lowered_path.endswith(".log"):
        return 7

    if lowered_path.endswith((".md", ".txt")):
        return 7

    if lowered_path.endswith((".py", ".js", ".java", ".go")):
        return 6

    return 5


def get_context_bonus(context: dict) -> int:
    environment_hint = context.get("environment_hint")
    keywords = context.get("context_keywords", [])

    bonus = 0

    if environment_hint == "production":
        bonus += 10

    if "authorization" in keywords:
        bonus += 5

    if "cloud" in keywords:
        bonus += 5

    if "client_secret" in keywords:
        bonus += 4

    return bonus


def get_file_criticality_bonus(context: dict) -> int:
    file_criticality = context.get("file_criticality")

    if file_criticality == "high":
        return 10

    if file_criticality == "medium":
        return 5

    return 2


def build_frequency_map(findings: list[dict]) -> dict[str, int]:
    frequency_map = {}

    for finding in findings:
        secret_type = finding["secret_type"]
        frequency_map[secret_type] = frequency_map.get(secret_type, 0) + 1

    return frequency_map


def get_frequency_bonus(finding: dict, frequency_map: dict[str, int]) -> int:
    secret_type = finding["secret_type"]
    count = frequency_map.get(secret_type, 0)

    if count >= 3:
        return 10

    if count == 2:
        return 5

    return 0


def get_risk_level(risk_score: int) -> str:
    if risk_score >= 90:
        return "Critical"

    if risk_score >= 70:
        return "High"

    if risk_score >= 40:
        return "Medium"

    return "Low"
