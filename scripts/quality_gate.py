import subprocess
import sys
from pathlib import Path

PYTHON = sys.executable

REQUIRED_FILES = [
    "app/main.py",
    "app/agents/state.py",
    "app/agents/graph.py",
    "app/agents/nodes/discovery_node.py",
    "app/agents/nodes/context_node.py",
    "app/agents/nodes/risk_node.py",
    "app/agents/nodes/policy_node.py",
    "app/agents/nodes/explanation_node.py",
    "app/agents/nodes/review_node.py",
    "app/agents/nodes/report_node.py",
    "app/scanner/secret_scanner.py",
    "app/scanner/masking.py",
    "app/policy/policy_retriever.py",
    "app/review/review_manager.py",
    "frontend/streamlit_app.py",
    "scripts/create_sample_project.py",
    "tests/test_graph_run.py",
    "tests/test_masking.py",
    "tests/test_policy_retriever.py",
    "tests/test_review_manager.py",
    "README.md",
    ".gitignore",
    "pyproject.toml",
]


RAW_SECRET_PATTERNS = [
    "AKIA" + "1234567890ABCDEF",
    "ghp_" + "abcdefghijklmnopqrstuvwxyz1234567890",
    "sample_client_secret_" + "abcdefghijklmnopqrstuvwxyz",
    "sampleBearerToken" + "1234567890abcdef",
]


def main() -> None:
    print("=== NHI Secret Agent Quality Gate ===")

    assert_required_files_exist()
    assert_sample_project_tracking_is_safe()
    assert_report_outputs_are_not_tracked()
    assert_raw_secret_patterns_are_not_tracked()
    assert_generated_reports_do_not_contain_raw_secrets()

    run_command([PYTHON, "-m", "pytest", "-q"])
    run_command([PYTHON, "-m", "ruff", "format", "--check", "app", "tests", "scripts", "frontend"])
    run_command([PYTHON, "-m", "ruff", "check", "app", "tests", "scripts", "frontend"])

    print("\n[PASS] Quality gate completed successfully.")


def assert_required_files_exist() -> None:
    print("\n[CHECK] Required files")

    missing_files = [file_path for file_path in REQUIRED_FILES if not Path(file_path).exists()]

    if missing_files:
        fail("Missing required files:\n" + "\n".join(f"- {file_path}" for file_path in missing_files))

    print("[PASS] Required files exist.")


def assert_sample_project_tracking_is_safe() -> None:
    print("\n[CHECK] data/sample_project tracking")

    tracked_files = get_git_ls_files("data/sample_project")
    expected_files = ["data/sample_project/.gitkeep"]

    if tracked_files != expected_files:
        fail(f"data/sample_project should only track .gitkeep.\nExpected: {expected_files}\nActual: {tracked_files}")

    print("[PASS] data/sample_project only tracks .gitkeep.")


def assert_report_outputs_are_not_tracked() -> None:
    print("\n[CHECK] reports tracking")

    tracked_files = get_git_ls_files("reports")
    allowed_files = {"reports/.gitkeep"}

    unexpected_files = [file_path for file_path in tracked_files if file_path not in allowed_files]

    if unexpected_files:
        fail(
            "Generated report files must not be tracked by Git:\n"
            + "\n".join(f"- {file_path}" for file_path in unexpected_files)
        )

    print("[PASS] reports output files are not tracked.")


def assert_raw_secret_patterns_are_not_tracked() -> None:
    print("\n[CHECK] raw-looking secret patterns in tracked files")

    for pattern in RAW_SECRET_PATTERNS:
        result = subprocess.run(
            ["git", "grep", "-n", pattern, "--", "."],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode == 0 and result.stdout.strip():
            fail(f"Raw-looking secret pattern found in tracked files:\n{result.stdout}")

        if result.returncode not in {0, 1}:
            fail(f"git grep failed:\n{result.stderr}")

    print("[PASS] No raw-looking secret patterns found in tracked files.")


def assert_generated_reports_do_not_contain_raw_secrets() -> None:
    print("\n[CHECK] generated reports do not contain raw-looking secrets")

    report_files = [
        Path("reports/result.json"),
        Path("reports/report.md"),
        Path("reports/review_status.json"),
        Path("reports/audit_log.jsonl"),
    ]

    existing_report_files = [path for path in report_files if path.exists()]

    if not existing_report_files:
        print("[SKIP] No generated report files found.")
        return

    for path in existing_report_files:
        text = path.read_text(encoding="utf-8")

        for pattern in RAW_SECRET_PATTERNS:
            if pattern in text:
                fail(f"Raw-looking secret pattern found in generated file: {path}")

    print("[PASS] Generated reports do not contain raw-looking secrets.")


def get_git_ls_files(path: str) -> list[str]:
    result = run_command(
        ["git", "ls-files", path],
        capture_output=True,
    )

    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def run_command(command: list[str], capture_output: bool = False) -> subprocess.CompletedProcess:
    print(f"[RUN] {' '.join(command)}")

    result = subprocess.run(
        command,
        capture_output=capture_output,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        stdout = result.stdout if result.stdout else ""
        stderr = result.stderr if result.stderr else ""
        fail(f"Command failed:\n{' '.join(command)}\n\nSTDOUT:\n{stdout}\n\nSTDERR:\n{stderr}")

    return result


def fail(message: str) -> None:
    print(f"\n[FAIL] {message}")
    sys.exit(1)


if __name__ == "__main__":
    main()
