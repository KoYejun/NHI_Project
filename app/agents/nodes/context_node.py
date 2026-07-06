from app.agents.state import AgentState


def context_node(state: AgentState) -> AgentState:
    """
    Context Analysis Node.

    역할:
    - Secret이 발견된 파일 경로, 파일 유형, 환경 단서, 주변 문맥을 분석한다.
    - 실제 파일 본문 분석은 1번 담당자와 연동 후 확장한다.
    - 2단계에서는 파일 경로와 Secret 유형을 기준으로 규칙 기반 문맥 분석을 수행한다.
    """

    try:
        print("[Context Analysis Node] 실행")

        context_results = []

        for finding in state["raw_findings"]:
            file_path = finding["file_path"]
            secret_type = finding["secret_type"]

            file_type = classify_file_type(file_path)
            environment_hint = infer_environment(file_path, secret_type)
            file_criticality = infer_file_criticality(file_path)
            context_keywords = infer_context_keywords(file_path, secret_type)

            context_results.append(
                {
                    "finding_id": finding["finding_id"],
                    "environment_hint": environment_hint,
                    "file_type": file_type,
                    "file_criticality": file_criticality,
                    "context_keywords": context_keywords,
                    "context_summary": build_context_summary(
                        file_path=file_path,
                        secret_type=secret_type,
                        file_type=file_type,
                        environment_hint=environment_hint,
                    ),
                }
            )

        state["context_results"] = context_results

        return state

    except Exception as exc:
        state["errors"].append(f"Context Node Error: {str(exc)}")
        return state


def classify_file_type(file_path: str) -> str:
    if file_path.endswith(".env"):
        return "config"
    if file_path.endswith((".yml", ".yaml", ".json", ".ini")):
        return "config"
    if file_path.endswith(".log"):
        return "log"
    if file_path.endswith((".md", ".txt")):
        return "document"
    if file_path.endswith((".py", ".js", ".java", ".go")):
        return "source_code"
    return "unknown"


def infer_environment(file_path: str, secret_type: str) -> str:
    lowered_path = file_path.lower()

    if ".env" in lowered_path and secret_type == "AWS_ACCESS_KEY_ID":
        return "production"

    if "prod" in lowered_path or "production" in lowered_path:
        return "production"

    if "dev" in lowered_path or "test" in lowered_path:
        return "development"

    return "unknown"


def infer_file_criticality(file_path: str) -> str:
    lowered_path = file_path.lower()

    if lowered_path.endswith(".env"):
        return "high"

    if lowered_path.endswith((".yml", ".yaml", ".json", ".ini")):
        return "high"

    if lowered_path.endswith(".log"):
        return "medium"

    if lowered_path.endswith((".py", ".js", ".java", ".go")):
        return "medium"

    if lowered_path.endswith((".md", ".txt")):
        return "medium"

    return "low"


def infer_context_keywords(file_path: str, secret_type: str) -> list[str]:
    keywords = []

    lowered_path = file_path.lower()

    if ".env" in lowered_path:
        keywords.extend(["env", "configuration"])

    if "config" in lowered_path:
        keywords.append("config")

    if "log" in lowered_path:
        keywords.append("log")

    if secret_type == "AWS_ACCESS_KEY_ID":
        keywords.extend(["cloud", "aws", "access_key"])

    elif secret_type == "GITHUB_TOKEN":
        keywords.extend(["github", "repository", "ci_cd"])

    elif secret_type == "GENERIC_CLIENT_SECRET":
        keywords.extend(["oauth", "client_secret"])

    elif secret_type == "BEARER_TOKEN":
        keywords.extend(["authorization", "bearer_token", "api"])

    return keywords


def build_context_summary(
    file_path: str,
    secret_type: str,
    file_type: str,
    environment_hint: str,
) -> str:
    return (
        f"{file_type} 파일인 {file_path}에서 {secret_type} 유형의 Secret 후보가 발견되었습니다. "
        f"환경 단서는 {environment_hint}로 추정됩니다."
    )
