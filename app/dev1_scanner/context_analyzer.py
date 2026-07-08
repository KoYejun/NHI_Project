from pathlib import Path
from typing import Any

KEYWORD_CATEGORIES = {
    "production": {
        "production",
        "prod",
        "live",
        "real",
    },
    "privileged_account": {
        "admin",
        "root",
        "privileged",
        "owner",
        "superuser",
    },
    "data_store": {
        "database",
        "db",
        "datastore",
        "backup",
        "storage",
    },
    "sensitive_term": {
        "secret",
        "token",
        "password",
        "credential",
        "bearer",
        "key",
    },
}


def analyze(file_path: str, line_number: int) -> dict[str, Any]:
    """
    Secret이 발견된 파일과 주변 문맥을 분석한다.
    """

    actual_path = resolve_actual_path(file_path)
    file_type = classify_file_type(actual_path)

    text = read_context_text(actual_path, line_number, file_type)
    environment = guess_environment(actual_path, text)
    keywords_found = find_keyword_categories(text)

    return {
        "file_type": file_type,
        "environment": environment,
        "keywords_found": keywords_found,
    }


def resolve_actual_path(file_path: str) -> Path:
    path = Path(file_path)

    if path.exists():
        return path

    data_path = Path("data") / path

    if data_path.exists():
        return data_path

    return path


def classify_file_type(file_path: Path) -> str:
    file_name = file_path.name.lower()
    suffix = file_path.suffix.lower()

    if file_name == ".env" or suffix == ".env":
        return "env"

    if suffix in {".yml", ".yaml", ".json", ".ini"}:
        return "config"

    if suffix in {".py", ".js", ".java", ".go"}:
        return "code"

    if suffix == ".log":
        return "log"

    if suffix in {".md", ".txt"}:
        return "doc"

    return "other"


def guess_environment(file_path: Path, text: str) -> str:
    combined = f"{file_path.as_posix()}\n{text}".lower()

    if any(keyword in combined for keyword in ["production", "/prod/", "prod-", "prod_"]):
        return "prod"

    if any(keyword in combined for keyword in ["development", "/dev/", "dev-", "dev_"]):
        return "dev"

    if any(keyword in combined for keyword in ["test", "/test/", "staging"]):
        return "test"

    return "unknown"


def read_context_text(file_path: Path, line_number: int, file_type: str) -> str:
    try:
        lines = file_path.read_text(encoding="utf-8").splitlines()
    except (FileNotFoundError, UnicodeDecodeError):
        return ""

    if file_type in {"env", "config"}:
        return "\n".join(lines)

    start_index = max(line_number - 4, 0)
    end_index = min(line_number + 3, len(lines))

    return "\n".join(lines[start_index:end_index])


def find_keyword_categories(text: str) -> list[str]:
    lowered_text = text.lower()
    categories = []

    for category, keywords in KEYWORD_CATEGORIES.items():
        if any(keyword in lowered_text for keyword in keywords):
            categories.append(category)

    return categories
