from typing import Any

TYPE_RISK = {
    "PRIVATE_KEY": 10,
    "AWS_ACCESS_KEY": 10,
    "AWS_ACCESS_KEY_ID": 10,
    "GITHUB_TOKEN": 9,
    "SLACK_BOT_TOKEN": 8,
    "BEARER_TOKEN": 6,
    "GENERIC_API_KEY": 5,
    "HIGH_ENTROPY_STRING": 4,
}


def calculate_risk(
    secret_type: str,
    context: dict[str, Any],
    occurrence_count: int,
) -> dict[str, Any]:
    type_risk = TYPE_RISK.get(secret_type, 4)
    exposure = exposure_risk(context)
    base_score = type_risk * exposure
    context_score = context_bonus(context)
    file_score = file_criticality_bonus(context)
    frequency_score = frequency_bonus(occurrence_count)

    total_score = base_score + context_score + file_score + frequency_score
    normalized_score = min(int(total_score), 100)

    return {
        "type_risk": type_risk,
        "exposure_risk": exposure,
        "base_score": round(base_score, 1),
        "context_bonus": context_score,
        "file_criticality_bonus": file_score,
        "frequency_bonus": frequency_score,
        "score": normalized_score,
        "grade": classify_grade(normalized_score),
    }


def exposure_risk(context: dict[str, Any]) -> float:
    file_type = context.get("file_type", "other")
    environment = context.get("environment", "unknown")

    if environment == "prod":
        if file_type == "env":
            return 3.0

    mapping = {
        "env": 3.0,
        "config": 2.5,
        "code": 2.0,
        "log": 1.8,
        "doc": 1.3,
        "other": 1.0,
    }

    return mapping.get(file_type, 1.0)


def context_bonus(context: dict[str, Any]) -> int:
    keywords = set(context.get("keywords_found", []))

    score = 0

    if "production" in keywords:
        score += 15

    if "privileged_account" in keywords:
        score += 10

    if "data_store" in keywords:
        score += 8

    if "sensitive_term" in keywords:
        score += 5

    return min(score, 30)


def file_criticality_bonus(context: dict[str, Any]) -> int:
    file_type = context.get("file_type", "other")

    mapping = {
        "env": 25,
        "config": 20,
        "log": 15,
        "code": 12,
        "doc": 0,
        "other": 0,
    }

    return mapping.get(file_type, 0)


def frequency_bonus(occurrence_count: int) -> int:
    if occurrence_count >= 7:
        return 15

    if occurrence_count >= 4:
        return 10

    if occurrence_count >= 2:
        return 5

    return 0


def classify_grade(score: int) -> str:
    if score >= 90:
        return "Critical"

    if score >= 70:
        return "High"

    if score >= 40:
        return "Medium"

    if score >= 1:
        return "Low"

    return "Low"
