from pathlib import Path
from typing import Any

DEFAULT_POLICY_DOCUMENTS = [
    {
        "policy_id": "secret_management_policy",
        "title": "Secret Management Policy",
        "text": (
            "Secret, API Key, Access Token, Client Secret, Private Key는 소스코드, 설정 파일, "
            "문서, 로그에 평문으로 저장하지 않는다. Secret 노출 시 폐기 및 재발급을 검토하고, "
            "리포트에는 Secret 원문을 저장하지 않는다."
        ),
    },
    {
        "policy_id": "nhi_access_policy",
        "title": "NHI Access Policy",
        "text": (
            "Non-Human Identity는 최소권한 원칙에 따라 관리한다. 고위험 Secret이 발견되면 "
            "서비스 계정, 자동화 계정, 토큰 범위, 최근 접근 로그를 점검한다."
        ),
    },
    {
        "policy_id": "incident_response_policy",
        "title": "Incident Response Policy",
        "text": (
            "Critical 또는 High 위험 항목은 관리자 검토 대상으로 분류한다. 자동 폐기 또는 "
            "권한 회수는 수행하지 않고, 판단 근거와 대응 이력을 감사 가능한 형태로 기록한다."
        ),
    },
]


def retrieve_policy_evidence(
    risk_results: list[dict[str, Any]],
    context_results: list[dict[str, Any]],
    policy_dir: str = "data/policies",
    top_k: int = 3,
) -> list[dict[str, Any]]:
    """
    각 finding에 대해 관련 정책 근거를 검색한다.

    현재 구현은 벡터DB 기반 RAG가 아니라 keyword 기반 RAG-lite 방식이다.
    외부 API 호출이 없고, 로컬 정책 문서만 사용한다.
    """

    policies = load_policy_documents(policy_dir)
    context_map = {item["finding_id"]: item for item in context_results}

    evidence_results = []

    for risk in risk_results:
        finding_id = risk["finding_id"]
        context = context_map.get(finding_id, {})
        keywords = build_policy_keywords(risk, context)

        matched_policies = find_relevant_policies(
            policies=policies,
            keywords=keywords,
            top_k=top_k,
        )

        evidence_results.append(
            {
                "finding_id": finding_id,
                "query_keywords": sorted(keywords),
                "matched_policies": matched_policies,
            }
        )

    return evidence_results


def load_policy_documents(policy_dir: str) -> list[dict[str, str]]:
    policy_path = Path(policy_dir)

    if not policy_path.exists():
        return DEFAULT_POLICY_DOCUMENTS

    markdown_files = sorted(policy_path.glob("*.md"))

    if not markdown_files:
        return DEFAULT_POLICY_DOCUMENTS

    documents = []

    for file_path in markdown_files:
        text = file_path.read_text(encoding="utf-8")
        title = extract_title(text, file_path.stem)

        documents.append(
            {
                "policy_id": file_path.stem,
                "title": title,
                "text": text,
            }
        )

    return documents


def extract_title(text: str, fallback: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped.replace("# ", "", 1).strip()

    return fallback


def build_policy_keywords(risk: dict[str, Any], context: dict[str, Any]) -> set[str]:
    keywords = {
        "secret",
        "token",
        "credential",
        "manager",
        "review",
        "log",
    }

    secret_type = risk.get("secret_type", "")
    risk_level = risk.get("risk_level", "")
    file_path = risk.get("file_path", "")
    context_keywords = context.get("context_keywords", [])
    environment_hint = context.get("environment_hint", "")

    if secret_type == "AWS_ACCESS_KEY_ID":
        keywords.update({"aws", "cloud", "access", "key", "iam", "nhi"})

    if secret_type == "GITHUB_TOKEN":
        keywords.update({"github", "repository", "ci", "cd", "actions", "automation"})

    if secret_type == "GENERIC_CLIENT_SECRET":
        keywords.update({"client", "oauth", "api", "application"})

    if secret_type == "BEARER_TOKEN":
        keywords.update({"bearer", "authorization", "api", "header", "log"})

    if risk_level in {"Critical", "High"}:
        keywords.update({"critical", "high", "human", "approval", "incident"})

    if environment_hint == "production":
        keywords.update({"production", "operating", "environment"})

    if file_path.endswith(".env"):
        keywords.update({"env", "configuration", "secret"})

    if file_path.endswith(".log"):
        keywords.update({"log", "incident", "response"})

    for keyword in context_keywords:
        keywords.add(str(keyword).lower())

    return keywords


def find_relevant_policies(
    policies: list[dict[str, str]],
    keywords: set[str],
    top_k: int,
) -> list[dict[str, Any]]:
    scored_policies = []

    for policy in policies:
        score = calculate_keyword_score(policy["text"], keywords)

        if score <= 0:
            continue

        scored_policies.append(
            {
                "policy_id": policy["policy_id"],
                "title": policy["title"],
                "summary": build_policy_summary(policy["text"]),
                "relevance_score": round(score, 3),
            }
        )

    scored_policies.sort(
        key=lambda item: item["relevance_score"],
        reverse=True,
    )

    if scored_policies:
        return scored_policies[:top_k]

    return [
        {
            "policy_id": "no_policy_match",
            "title": "No Policy Match",
            "summary": "관련 정책 근거를 찾지 못했습니다. 보안 담당자 검토가 필요합니다.",
            "relevance_score": 0.0,
        }
    ]


def calculate_keyword_score(text: str, keywords: set[str]) -> float:
    lowered_text = text.lower()
    matched_count = 0

    for keyword in keywords:
        if keyword.lower() in lowered_text:
            matched_count += 1

    if not keywords:
        return 0.0

    return matched_count / len(keywords)


def build_policy_summary(text: str, max_length: int = 160) -> str:
    normalized = " ".join(line.strip() for line in text.splitlines() if line.strip())

    if len(normalized) <= max_length:
        return normalized

    return normalized[:max_length].rstrip() + "..."
