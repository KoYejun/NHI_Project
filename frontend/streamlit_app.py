import importlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = PROJECT_ROOT / "reports" / "result.json"
SAMPLE_SCRIPT_PATH = PROJECT_ROOT / "scripts" / "create_sample_project.py"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

os.chdir(PROJECT_ROOT)

graph_module = importlib.import_module("app.agents.graph")
review_manager = importlib.import_module("app.review.review_manager")

build_graph = graph_module.build_graph
get_effective_review_status = review_manager.get_effective_review_status
load_review_status = review_manager.load_review_status
read_audit_logs = review_manager.read_audit_logs
save_review_decision = review_manager.save_review_decision


PALETTE = {
    "teal": "#10C8B0",
    "blue": "#2870E0",
    "yellow": "#F8D820",
    "dark": "#172033",
    "muted": "#5C667A",
    "bg": "#F7FAFC",
    "card": "#FFFFFF",
    "line": "#E4EAF2",
}


def main() -> None:
    st.set_page_config(
        page_title="NHI Secret Agent Dashboard",
        page_icon="🛡️",
        layout="wide",
    )

    apply_styles()

    st.markdown(
        """
        <div class="hero">
            <div class="hero-kicker">NHI Secret Agent</div>
            <div class="hero-title">
                프로젝트 파일 속에 숨어 있는 비밀키를 찾아내고, 어떤 항목부터 확인해야 하는지 알려줍니다.
            </div>
            <div class="hero-desc">
                이 대시보드는 코드, 설정 파일, 로그, 문서 안에 남아 있을 수 있는 Secret을 자동으로 탐지합니다.
                탐지된 값은 원문이 노출되지 않도록 마스킹하고, 발견 위치와 주변 문맥을 함께 분석해 위험도를 계산합니다.
                이후 정책 근거, 대응 권고, 관리자 검토 상태, 감사 로그까지 이어지는 전체 보안 점검 흐름을 한 화면에서 확인할 수 있습니다.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    render_sidebar()
    render_process_strip()

    result = load_result_if_exists()

    if result is None:
        render_empty_state()
        return

    findings = result.get("findings", [])
    summary = result.get("summary", {})
    saved_review_status = load_review_status()

    if not findings:
        st.warning("분석 결과 파일은 있지만 Finding이 없습니다.")
        st.json(result)
        return

    findings_df = build_findings_dataframe(findings, saved_review_status)
    risk_df = build_risk_dataframe(findings)
    policy_df = build_policy_dataframe(findings)
    audit_df = build_audit_dataframe()

    render_scroll_story(
        summary=summary,
        findings=findings,
        findings_df=findings_df,
        risk_df=risk_df,
        policy_df=policy_df,
        audit_df=audit_df,
        saved_review_status=saved_review_status,
        result=result,
    )


def apply_styles() -> None:
    st.markdown(
        f"""
        <style>
        :root {{
            --teal: {PALETTE["teal"]};
            --blue: {PALETTE["blue"]};
            --yellow: {PALETTE["yellow"]};
            --dark: {PALETTE["dark"]};
            --muted: {PALETTE["muted"]};
            --bg: {PALETTE["bg"]};
            --card: {PALETTE["card"]};
            --line: {PALETTE["line"]};
        }}

        .stApp {{
            background:
                radial-gradient(circle at 10% 5%, rgba(16, 200, 176, 0.12), transparent 28%),
                radial-gradient(circle at 88% 2%, rgba(40, 112, 224, 0.12), transparent 24%),
                linear-gradient(180deg, #ffffff 0%, var(--bg) 100%);
        }}

        .block-container {{
            max-width: 1180px;
            padding-top: 2.2rem;
            padding-bottom: 4rem;
        }}

        .hero {{
            border: 1px solid var(--line);
            border-radius: 28px;
            padding: 34px 38px;
            background:
                linear-gradient(135deg, rgba(16, 200, 176, 0.10), rgba(40, 112, 224, 0.08)),
                #ffffff;
            box-shadow: 0 18px 48px rgba(23, 32, 51, 0.08);
            margin-bottom: 24px;
            position: relative;
            overflow: hidden;
        }}

        .hero:after {{
            content: "";
            position: absolute;
            right: -42px;
            top: -56px;
            width: 180px;
            height: 180px;
            border: 12px solid rgba(248, 216, 32, 0.55);
            border-radius: 50%;
            transform: rotate(-18deg);
        }}

        .hero-kicker {{
            display: inline-block;
            color: #ffffff;
            background: linear-gradient(90deg, var(--teal), var(--blue));
            border-radius: 999px;
            padding: 7px 14px;
            font-weight: 700;
            font-size: 13px;
            margin-bottom: 16px;
        }}

        .hero-title {{
            color: var(--dark);
            font-size: 34px;
            font-weight: 850;
            line-height: 1.22;
            letter-spacing: -0.04em;
            max-width: 840px;
        }}

        .hero-desc {{
            color: var(--muted);
            font-size: 16px;
            line-height: 1.65;
            margin-top: 14px;
            max-width: 860px;
        }}

        .process-strip {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 12px;
            margin: 18px 0 34px 0;
        }}

                .process-card {{
            border: 1px solid var(--line);
            border-radius: 22px;
            padding: 22px 20px;
            background: #ffffff;
            box-shadow: 0 12px 32px rgba(23, 32, 51, 0.06);
            min-height: 178px;
        }}

        .process-number {{
            width: 36px;
            height: 36px;
            border-radius: 13px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            color: #ffffff;
            background: linear-gradient(135deg, var(--teal), var(--blue));
            font-weight: 900;
            font-size: 18px;
            margin-bottom: 14px;
        }}

        .process-title {{
            font-size: 22px;
            font-weight: 900;
            color: var(--dark);
            margin-bottom: 10px;
            letter-spacing: -0.035em;
        }}

        .process-desc {{
            color: var(--muted);
            font-size: 15px;
            line-height: 1.6;
        }}

        .story-section {{
            border: 1px solid var(--line);
            border-radius: 30px;
            background: #ffffff;
            padding: 34px 34px 28px 34px;
            margin: 32px 0;
            box-shadow: 0 18px 42px rgba(23, 32, 51, 0.06);
        }}

        .story-section.accent-teal {{
            border-top: 7px solid var(--teal);
        }}

        .story-section.accent-blue {{
            border-top: 7px solid var(--blue);
        }}

        .story-section.accent-yellow {{
            border-top: 7px solid var(--yellow);
        }}

        .section-label {{
            display: inline-block;
            border-radius: 999px;
            padding: 6px 12px;
            background: rgba(16, 200, 176, 0.10);
            color: var(--blue);
            font-weight: 800;
            font-size: 12px;
            margin-bottom: 14px;
        }}

                .big-result {{
            color: var(--dark);
            font-size: 36px;
            font-weight: 900;
            line-height: 1.25;
            letter-spacing: -0.04em;
            margin-bottom: 14px;
        }}

        .section-summary {{
            color: var(--muted);
            font-size: 17px;
            line-height: 1.75;
            margin-bottom: 24px;
        }}

        .metric-row {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 12px;
            margin: 14px 0 22px 0;
        }}

        .metric-card {{
            border: 1px solid var(--line);
            border-radius: 18px;
            padding: 15px;
            background: linear-gradient(180deg, #ffffff, #fbfdff);
        }}

        .metric-label {{
            color: var(--muted);
            font-size: 12px;
            font-weight: 700;
            margin-bottom: 6px;
        }}

        .metric-value {{
            color: var(--dark);
            font-size: 24px;
            font-weight: 850;
        }}

        .explain-note {{
            color: var(--muted);
            font-size: 14px;
            line-height: 1.6;
        }}

        div[data-testid="stExpander"] {{
            border: 1px solid var(--line);
            border-radius: 16px;
            background: #fbfdff;
        }}

        div[data-testid="stDownloadButton"] button {{
            border-radius: 999px;
            border: 1px solid var(--line);
            color: var(--blue);
            background: #ffffff;
            font-weight: 700;
        }}

        div[data-testid="stButton"] button {{
            border-radius: 999px;
            font-weight: 800;
        }}

        @media (max-width: 900px) {{
            .process-strip {{
                grid-template-columns: 1fr;
            }}

            .metric-row {{
                grid-template-columns: 1fr 1fr;
            }}

            .hero-title {{
                font-size: 27px;
            }}

            .big-result {{
                font-size: 26px;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar() -> None:
    st.sidebar.header("Analysis Control")

    target_path = st.sidebar.text_input(
        "분석 대상 폴더",
        value="data/sample_project",
        help="스캐너가 읽을 대상 폴더입니다. 팀원 노트북에서도 기본값 그대로 실행할 수 있습니다.",
    )

    st.sidebar.markdown("### 실행 순서")
    st.sidebar.markdown(
        """
        1. 샘플 프로젝트 생성  
        2. 전체 분석 실행  
        3. 스크롤하며 결과 확인  
        4. Review 결정 저장  
        5. Audit Log 확인
        """
    )

    if st.sidebar.button("1. Create Sample Project", use_container_width=True):
        create_sample_project()

    if st.sidebar.button("2. Run Analysis", type="primary", use_container_width=True):
        run_analysis(target_path)

    if st.sidebar.button("Refresh Result", use_container_width=True):
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 생성 파일")
    st.sidebar.code(
        "reports/raw_findings.json\n"
        "reports/risk_results.json\n"
        "reports/result.json\n"
        "reports/report.md\n"
        "reports/review_status.json\n"
        "reports/audit_log.jsonl"
    )


def create_sample_project() -> None:
    with st.spinner("샘플 프로젝트를 생성하는 중입니다..."):
        result = subprocess.run(
            [sys.executable, str(SAMPLE_SCRIPT_PATH)],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    if result.returncode != 0:
        st.sidebar.error("샘플 프로젝트 생성 실패")
        st.sidebar.code(result.stderr or result.stdout)
        return

    st.sidebar.success("샘플 프로젝트 생성 완료")
    st.rerun()


def run_analysis(target_path: str) -> None:
    resolved_target_path = resolve_target_path(target_path)

    if not resolved_target_path.exists():
        st.sidebar.error(f"분석 대상 폴더가 없습니다: {target_path}")
        st.sidebar.info("먼저 Create Sample Project를 실행하세요.")
        return

    with st.spinner("Secret 탐지, 위험도 계산, Agent 분석, Human Review 분류를 실행하는 중입니다..."):
        initial_state = {
            "target_path": target_path,
            "raw_findings": [],
            "context_results": [],
            "risk_results": [],
            "policy_evidence": [],
            "explanations": [],
            "review_results": [],
            "report_path": "",
            "errors": [],
        }

        graph = build_graph()
        final_state = graph.invoke(initial_state)

    if final_state.get("errors"):
        st.sidebar.error("분석 중 오류 발생")
        st.sidebar.code("\n".join(final_state["errors"]))
        return

    st.sidebar.success(f"분석 완료: {len(final_state['raw_findings'])}건 탐지")
    st.rerun()


def resolve_target_path(target_path: str) -> Path:
    path = Path(target_path)

    if path.is_absolute():
        return path

    return PROJECT_ROOT / path


def load_result_if_exists() -> dict[str, Any] | None:
    if not REPORT_PATH.exists():
        return None

    try:
        return json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        st.error("reports/result.json 파일을 읽을 수 없습니다.")
        return None


def render_process_strip() -> None:
    st.markdown(
        """
        <div class="process-strip">
            <div class="process-card">
                <div class="process-number">1</div>
                <div class="process-title">Secret 탐지</div>
                <div class="process-desc">
                    분석 대상 폴더의 코드, 설정 파일, 로그, 문서를 훑어보며
                    비밀키처럼 보이는 값을 찾습니다. 알려진 패턴뿐 아니라
                    랜덤성이 높은 문자열도 함께 확인합니다.
                </div>
            </div>
            <div class="process-card">
                <div class="process-number">2</div>
                <div class="process-title">문맥 확인</div>
                <div class="process-desc">
                    같은 Secret이라도 어디에서 발견됐는지에 따라 위험도가 달라집니다.
                    운영 환경 파일인지, 관리자 계정이나 데이터베이스와 관련된 문맥인지 함께 확인합니다.
                </div>
            </div>
            <div class="process-card">
                <div class="process-number">3</div>
                <div class="process-title">위험도 판단</div>
                <div class="process-desc">
                    Secret 유형, 파일 위치, 주변 키워드, 반복 노출 여부를 기준으로
                    위험 점수를 계산합니다. 결과는 Critical, High, Medium, Low 등급으로 정리됩니다.
                </div>
            </div>
            <div class="process-card">
                <div class="process-number">4</div>
                <div class="process-title">검토와 기록</div>
                <div class="process-desc">
                    위험도가 높은 항목은 자동으로 조치하지 않고 사람이 검토하도록 남겨둡니다.
                    검토 결과는 감사 로그에 기록되어 나중에 다시 확인할 수 있습니다.
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_empty_state() -> None:
    render_story_header(
        label="Ready",
        title="아직 분석 결과가 없습니다.",
        summary=(
            "왼쪽 사이드바에서 샘플 프로젝트를 생성한 뒤 Run Analysis를 실행하면 "
            "아래에 스크롤형 분석 결과 페이지가 자동으로 생성됩니다."
        ),
        accent="teal",
    )

    st.code(
        "streamlit run frontend/streamlit_app.py\n# 브라우저에서 Create Sample Project → Run Analysis 클릭",
        language="powershell",
    )

    close_story_section()


def render_scroll_story(
    summary: dict[str, Any],
    findings: list[dict[str, Any]],
    findings_df: pd.DataFrame,
    risk_df: pd.DataFrame,
    policy_df: pd.DataFrame,
    audit_df: pd.DataFrame,
    saved_review_status: dict[str, dict[str, Any]],
    result: dict[str, Any],
) -> None:
    render_executive_section(summary, findings_df)
    render_scanner_section(findings_df)
    render_risk_section(findings, risk_df)
    render_context_section(findings_df)
    render_policy_section(policy_df)
    render_detail_section(findings, saved_review_status)
    render_review_section(findings, findings_df, saved_review_status)
    render_audit_section(audit_df)
    render_raw_json_section(result)


def render_executive_section(summary: dict[str, Any], findings_df: pd.DataFrame) -> None:
    total = int(summary.get("total", len(findings_df)))
    critical = int(summary.get("Critical", 0))
    high = int(summary.get("High", 0))
    pending = int((findings_df["review_status"] == "WAITING_HUMAN_REVIEW").sum())

    render_story_header(
        label="Executive Summary",
        title=f"총 {total}건의 Secret 후보를 찾았고, {critical + high}건은 먼저 확인해야 합니다.",
        summary=(
            f"분석 결과 Critical {critical}건, High {high}건이 확인되었습니다. "
            f"이 중 현재 관리자 검토가 필요한 항목은 {pending}건입니다. "
            "아래 표에서 어떤 파일에서 어떤 유형의 Secret이 발견됐는지 바로 확인할 수 있습니다."
        ),
        accent="teal",
    )

    render_section_guide(
        title="전체 위험 현황",
        paragraphs=[
            "이 영역은 분석 결과를 가장 먼저 요약해서 보여줍니다. 프로젝트 폴더 안에서 Secret처럼 보이는 값이 몇 개 발견됐고, 그중 우선 확인해야 할 항목이 몇 개인지 알 수 있습니다.",
            "Critical과 High는 단순히 많이 위험해 보인다는 뜻이 아니라, 파일 위치와 주변 문맥까지 고려했을 때 보안 담당자가 먼저 확인해야 하는 항목입니다.",
            "아래 표는 전체 탐지 목록입니다. 탐지 방식, Secret 유형, 파일 경로, 위험 점수, 검토 상태를 함께 보여주기 때문에 전체 상황을 빠르게 파악할 수 있습니다.",
        ],
    )

    render_metric_row(
        [
            ("Total Findings", total),
            ("Critical", critical),
            ("High", high),
            ("Pending Review", pending),
        ]
    )

    overview_columns = [
        "finding_id",
        "detector",
        "secret_type",
        "file_path",
        "risk_score",
        "risk_level",
        "review_status",
    ]

    render_table_with_csv(
        df=findings_df[overview_columns],
        filename="executive_summary.csv",
    )

    with st.expander("설명", expanded=False):
        st.markdown(
            """
            이 영역은 **어떤 값이 Secret 후보로 탐지됐는지**를 보여줍니다.

            Secret은 코드 파일에만 있는 것이 아니라 설정 파일, 로그, 문서에도 남을 수 있습니다.  
            그래서 이 시스템은 분석 대상 폴더 안의 여러 파일을 자동으로 확인합니다.

            탐지는 두 가지 방식으로 진행됩니다.

            1. **정규식 기반 탐지**  
               AWS Key, GitHub Token처럼 형식이 정해져 있는 값을 찾습니다.

            2. **엔트로피 기반 탐지**  
               이름은 명확하지 않지만 랜덤성이 높아 비밀값처럼 보이는 문자열을 찾습니다.

            탐지 결과에는 실제 Secret 원문을 저장하지 않습니다.  
            대시보드와 리포트에는 마스킹된 값만 표시되므로 결과 화면을 공유해도 민감 값이 그대로 노출되지 않습니다.
            """
        )

    close_story_section()


def render_scanner_section(findings_df: pd.DataFrame) -> None:
    regex_count = int((findings_df["detector"] == "regex").sum())
    entropy_count = int((findings_df["detector"] == "entropy").sum())
    detector_count_text = format_detector_result(regex_count, entropy_count)

    render_story_header(
        label="Scanner Results",
        title=detector_count_text,
        summary=(
            "프로젝트 폴더 안의 코드, 설정 파일, 로그, 문서를 자동으로 검사했습니다. "
            "형식이 명확한 Secret은 정규식으로 찾고, 이름은 명확하지 않지만 랜덤성이 높은 값은 엔트로피 분석으로 찾아냅니다."
        ),
        accent="blue",
    )

    render_section_guide(
        title="어떤 값을 찾았는지 확인합니다",
        paragraphs=[
            "이 영역은 스캐너가 실제로 찾아낸 Secret 후보를 보여줍니다. 입력값은 개별 문자열이 아니라 프로젝트 폴더 전체입니다. 즉, 코드와 설정 파일, 로그, 문서를 한 번에 검사합니다.",
            "regex는 AWS Access Key, GitHub Token, Slack Token처럼 모양이 정해진 값을 찾습니다. entropy는 이름이 명확하지 않아도 문자와 숫자가 섞여 있고 무작위성이 높아 Secret일 가능성이 있는 값을 찾습니다.",
            "탐지된 값은 원문 그대로 저장하지 않습니다. masked_secret과 line_content에는 마스킹된 값만 표시되므로, 데모나 보고서에 포함하더라도 실제 Secret이 다시 노출될 위험을 줄일 수 있습니다.",
        ],
    )

    render_metric_row(
        [
            ("Regex Findings", regex_count),
            ("Entropy Findings", entropy_count),
            ("Secret Types", findings_df["secret_type"].nunique()),
            ("Affected Files", findings_df["file_path"].nunique()),
        ]
    )

    scanner_df = findings_df[
        [
            "finding_id",
            "detector",
            "secret_type",
            "file_path",
            "line_number",
            "masked_secret",
            "line_content",
        ]
    ]

    render_table_with_csv(
        df=scanner_df,
        filename="scanner_results.csv",
    )

    with st.expander("설명", expanded=False):
        st.markdown(
            """
            이 화면은 무엇을 탐지했는지를 보여주는 단계입니다.

            보안 사고에서 Secret은 보통 코드, 설정 파일, 로그, 문서에 흩어져 있습니다.  
            사람이 직접 모든 파일을 확인하기 어렵기 때문에 Scanner Engine이 먼저 후보를 찾아냅니다.

            이 프로젝트의 탐지는 두 가지 방식으로 구성됩니다.

            1. 정규식 기반 탐지  
               AWS Key, GitHub Token, Slack Token, Bearer Token처럼 형식이 비교적 명확한 Secret을 찾습니다.

            2. 엔트로피 기반 탐지    
               이름이 명확하지 않아도 문자와 숫자가 섞여 있고 랜덤성이 높은 문자열을 Secret 후보로 판단합니다.

            탐지 결과에는 원문이 아니라 마스킹된 값만 저장됩니다.  
            그래서 분석 리포트나 대시보드가 다시 유출되더라도 실제 Secret이 그대로 노출되지 않습니다.
            """
        )

    close_story_section()


def render_risk_section(findings: list[dict[str, Any]], risk_df: pd.DataFrame) -> None:
    top_finding = get_top_risk_finding(findings)

    if top_finding:
        title = (
            f"가장 위험한 항목은 {top_finding.get('risk_score')}점 "
            f"{top_finding.get('risk_level')} 등급의 {top_finding.get('secret_type')}입니다."
        )
    else:
        title = "위험도 산정 대상 항목이 없습니다."

    render_story_header(
        label="Risk Analysis",
        title=title,
        summary=(
            "탐지된 Secret 후보를 위험한 순서대로 정리했습니다. "
            "Secret 유형뿐 아니라 발견된 위치, 운영 환경 단서, 파일 중요도, 반복 노출 여부를 함께 반영합니다."
        ),
        accent="yellow",
    )

    render_section_guide(
        title="왜 이 항목이 더 위험한지 설명합니다",
        paragraphs=[
            "Secret이 발견됐다고 해서 모든 항목이 같은 수준으로 위험한 것은 아닙니다. 예를 들어 README에 적힌 예시 키와 운영 환경의 .env 파일에 있는 AWS Key는 대응 우선순위가 달라야 합니다.",
            "이 시스템은 Secret 유형, 발견 위치, 주변 문맥, 파일 중요도, 반복 노출 횟수를 함께 계산합니다. 그래서 단순 탐지 목록이 아니라 보안 담당자가 먼저 볼 항목부터 정렬된 결과를 제공합니다.",
            "점수는 TypeRisk, ExposureRisk, ContextBonus, FileCriticalityBonus, FrequencyBonus로 구성됩니다. 아래 표에서는 각 항목의 점수가 어떤 요소 때문에 높아졌는지 확인할 수 있습니다.",
        ],
    )

    risk_order = ["Critical", "High", "Medium", "Low"]
    risk_counts = risk_df["risk_level"].value_counts().reindex(risk_order, fill_value=0)

    render_metric_row(
        [
            ("Critical", int(risk_counts.get("Critical", 0))),
            ("High", int(risk_counts.get("High", 0))),
            ("Medium", int(risk_counts.get("Medium", 0))),
            ("Low", int(risk_counts.get("Low", 0))),
        ]
    )

    st.markdown("#### 위험도 분포")
    st.bar_chart(risk_counts)

    render_table_with_csv(
        df=risk_df,
        filename="risk_analysis.csv",
    )

    with st.expander("설명", expanded=False):
        st.markdown(
            """
            이 영역은 탐지된 항목이 **얼마나 위험한지**를 보여줍니다.

            Secret 후보가 발견되었다고 해서 모두 같은 수준으로 위험한 것은 아닙니다.  
            예를 들어 문서에 적힌 예시 키와 운영 환경의 설정 파일에 있는 실제 키는 대응 우선순위가 달라야 합니다.

            그래서 이 시스템은 다음 요소를 함께 봅니다.

            - **Secret 유형**: AWS Key인지, GitHub Token인지, 일반 API Key인지
            - **발견 위치**: .env, config, code, log, 문서 중 어디에서 발견됐는지
            - **주변 문맥**: production, admin, database 같은 단서가 있는지
            - **반복 노출**: 같은 값이 여러 파일에 반복해서 등장하는지

            이 요소들을 점수화해 Critical, High, Medium, Low 등급으로 나눕니다.  
            Critical과 High 항목은 사람이 먼저 확인해야 하는 검토 대상으로 분류됩니다.
            """
        )

    close_story_section()


def render_context_section(findings_df: pd.DataFrame) -> None:
    high_context_count = int(
        (
            (findings_df["environment_hint"] == "production")
            | (findings_df["file_criticality"] == "high")
            | findings_df["context_keywords"].str.contains("production|privileged|data_store", na=False)
        ).sum()
    )

    render_story_header(
        label="Context Analysis",
        title=f"발견 위치와 주변 문맥을 함께 봤을 때, {high_context_count}건은 주의가 필요합니다.",
        summary=(
            "Secret 후보가 단순 예시인지, 운영 환경과 연결된 민감 정보인지 구분하기 위해 파일 유형과 주변 키워드를 함께 확인했습니다."
        ),
        accent="teal",
    )

    render_section_guide(
        title="Secret이 발견된 상황을 함께 확인합니다",
        paragraphs=[
            "보안 탐지에서 중요한 것은 값을 찾는 것만이 아닙니다. 같은 문자열이라도 어디에서 발견됐는지, 주변에 어떤 단서가 있는지에 따라 실제 위험도가 달라집니다.",
            "이 영역은 Secret 후보가 .env, config, code, log, doc 중 어떤 파일에서 발견됐는지 보여줍니다. 또한 production, admin, root, database, token 같은 키워드가 주변에 있는지도 확인합니다.",
            "이 문맥 정보는 위험도 계산에 반영됩니다. 운영 환경 설정 파일에서 발견된 Secret은 더 높은 점수를 받고, 문서의 예시 값처럼 보이는 항목은 상대적으로 낮은 점수를 받을 수 있습니다.",
        ],
    )

    context_df = findings_df[
        [
            "finding_id",
            "secret_type",
            "file_path",
            "file_type",
            "environment_hint",
            "file_criticality",
            "context_keywords",
            "risk_level",
        ]
    ]

    render_table_with_csv(
        df=context_df,
        filename="context_analysis.csv",
    )

    with st.expander("설명", expanded=False):
        st.markdown(
            """
            <div class="explain-note">
            Context Analysis는 .env, config, log, code, doc 같은 파일 유형을 구분하고,
            production, admin, root, database, secret, token 같은 단서를 찾아 위험 점수에 반영합니다.
            이 구조 덕분에 README의 예시 키와 운영 환경 설정 파일의 Secret 후보를 다르게 평가할 수 있습니다.
            </div>
            """,
            unsafe_allow_html=True,
        )

    close_story_section()


def render_policy_section(policy_df: pd.DataFrame) -> None:
    matched_count = int(policy_df["matched_policy_count"].sum()) if not policy_df.empty else 0
    finding_count = int((policy_df["matched_policy_count"] > 0).sum()) if not policy_df.empty else 0

    render_story_header(
        label="Policy Evidence",
        title=f"탐지 결과 중 {finding_count}건에 대해 관련 보안 정책 근거를 연결했습니다.",
        summary=(
            f"총 {matched_count}개의 정책 근거가 연결되었습니다. "
            "이를 통해 단순히 위험하다고 표시하는 데서 끝나지 않고, 왜 검토나 조치가 필요한지 설명할 수 있습니다."
        ),
        accent="blue",
    )

    render_section_guide(
        title="왜 조치가 필요한지 근거를 보여줍니다",
        paragraphs=[
            "보안 담당자는 탐지 결과만으로 조치를 결정하기 어렵습니다. 어떤 정책이나 기준에 따라 검토해야 하는지 함께 제시되어야 합니다.",
            "이 영역은 Secret 관리 정책, NHI 접근 정책, 사고 대응 정책 등과 Finding을 연결합니다. 그래서 각 항목이 어떤 보안 원칙과 관련되는지 쉽게 확인할 수 있습니다.",
            "정책 근거는 로컬 문서를 기반으로 연결됩니다. 외부 API나 외부 LLM으로 분석 대상 코드나 Secret 원문을 보내지 않기 때문에 데모 환경에서도 안전하게 사용할 수 있습니다.",
        ],
    )

    render_table_with_csv(
        df=policy_df,
        filename="policy_evidence.csv",
    )

    with st.expander("설명", expanded=False):
        st.markdown(
            """
            <div class="explain-note">
            Policy Evidence는 로컬 정책 문서를 기반으로 각 Finding과 관련 있는 정책 근거를 연결합니다.
            대시보드에서는 어떤 정책이 어떤 Secret 후보와 연결되었는지 확인할 수 있고,
            이 결과는 Agent 설명의 policy_basis와 대응 권고에 반영됩니다.
            </div>
            """,
            unsafe_allow_html=True,
        )

    close_story_section()


def render_detail_section(
    findings: list[dict[str, Any]],
    saved_review_status: dict[str, dict[str, Any]],
) -> None:
    top_finding = get_top_risk_finding(findings)

    render_story_header(
        label="Finding Detail",
        title="선택한 항목의 탐지 근거와 위험 판단을 자세히 확인합니다.",
        summary=(
            "하나의 Finding을 선택하면 파일 경로, 탐지 라인, 점수 산정 근거, 문맥 분석, Agent 설명을 한 번에 볼 수 있습니다."
        ),
        accent="yellow",
    )

    render_section_guide(
        title="개별 항목을 자세히 살펴봅니다",
        paragraphs=[
            "전체 요약에서 위험한 항목을 확인했다면, 이 영역에서 해당 항목이 왜 탐지되었고 왜 위험하다고 판단됐는지 자세히 볼 수 있습니다.",
            "파일 경로와 라인 번호를 보면 Secret 후보가 어디에서 발견됐는지 알 수 있습니다. 탐지 라인은 마스킹된 형태로만 표시되어 실제 Secret 원문은 노출되지 않습니다.",
            "아래 설명 영역에서는 탐지 요약, 위험 판단, NHI 연결 가능성, 예상 영향, 대응 권고를 확인할 수 있습니다. 이 부분은 보안 담당자가 보고서처럼 바로 읽을 수 있도록 구성했습니다.",
        ],
    )

    finding_map = {finding["finding_id"]: finding for finding in findings}
    default_index = 0

    if top_finding:
        finding_ids = list(finding_map.keys())
        default_index = finding_ids.index(top_finding["finding_id"])

    selected_id = st.selectbox(
        "상세 확인할 Finding 선택",
        list(finding_map.keys()),
        index=default_index,
        format_func=lambda value: format_finding_label(finding_map[value]),
        key="detail_select",
    )

    finding = finding_map[selected_id]
    context = finding.get("context", {})
    score_detail = finding.get("score_detail", {})
    explanation = finding.get("agent_explanation", {})
    effective_review = get_effective_review_status(finding, saved_review_status)

    detail_rows = [
        ("Finding ID", finding.get("finding_id")),
        ("Detector", finding.get("detector")),
        ("Secret Type", finding.get("secret_type")),
        ("File Path", finding.get("file_path")),
        ("Line Number", finding.get("line_number")),
        ("Masked Secret", finding.get("masked_secret")),
        ("Occurrence Count", finding.get("occurrence_count", 1)),
        ("Risk", f"{finding.get('risk_level')} / {finding.get('risk_score')}"),
        ("Review Status", effective_review.get("current_status")),
        ("File Type", context.get("file_type")),
        ("Environment", context.get("environment_hint")),
        ("Context Keywords", ", ".join(context.get("context_keywords", []))),
        ("TypeRisk", score_detail.get("type_risk")),
        ("ExposureRisk", score_detail.get("exposure_risk")),
        ("ContextBonus", score_detail.get("context_bonus")),
        ("FileCriticalityBonus", score_detail.get("file_criticality_bonus")),
        ("FrequencyBonus", score_detail.get("frequency_bonus")),
    ]

    detail_df = pd.DataFrame(detail_rows, columns=["field", "value"])

    render_table_with_csv(
        df=detail_df,
        filename=f"{selected_id}_detail.csv",
    )

    st.markdown("#### 탐지 라인")
    st.code(finding.get("line_content", ""), language="text")

    with st.expander("설명", expanded=False):
        st.markdown("#### Agent 분석")
        st.write(f"**탐지 요약:** {explanation.get('summary')}")
        st.write(f"**위험 판단:** {explanation.get('risk_reason')}")
        st.write(f"**NHI 연결 가능성:** {explanation.get('nhi_possibility')}")
        st.write(f"**가능한 영향:** {explanation.get('possible_impact')}")
        st.write(f"**정책 근거 요약:** {explanation.get('policy_basis')}")
        st.write(f"**대응 권고:** {explanation.get('recommendation')}")
        st.write(f"**사람 검토:** {explanation.get('human_review')}")

    close_story_section()


def render_review_section(
    findings: list[dict[str, Any]],
    findings_df: pd.DataFrame,
    saved_review_status: dict[str, dict[str, Any]],
) -> None:
    review_df = findings_df[findings_df["requires_human_review"]]
    review_count = len(review_df)

    render_story_header(
        label="Human Review",
        title=f"위험도가 높은 {review_count}건은 사람이 최종 검토하도록 분리했습니다.",
        summary=(
            "Secret 후보를 찾았다고 해서 바로 폐기하거나 권한을 회수하지 않습니다. "
            "오탐 가능성과 서비스 영향도를 고려하기 위해 관리자 검토 단계를 둡니다."
        ),
        accent="teal",
    )

    render_section_guide(
        title="자동 탐지와 사람의 판단을 분리합니다",
        paragraphs=[
            "보안 자동화는 빠르게 위험 후보를 찾을 수 있지만, 실제 조치까지 자동으로 수행하면 문제가 생길 수 있습니다. 예를 들어 오탐이거나 이미 폐기된 값일 수도 있고, 서비스 운영에 영향을 줄 수도 있습니다.",
            "그래서 이 시스템은 Critical과 High 항목을 우선 검토 대상으로 분류하고, 최종 판단은 관리자가 남기도록 설계했습니다.",
            "검토자는 회전 승인, 오탐 처리, 위험 수용, 해결 완료 같은 상태를 저장할 수 있습니다. 이 결정은 이후 감사 로그에 남아 누가 어떤 판단을 했는지 추적할 수 있습니다.",
        ],
    )

    review_columns = [
        "finding_id",
        "secret_type",
        "file_path",
        "risk_score",
        "risk_level",
        "review_status",
        "reviewer",
        "reviewed_at",
    ]

    if review_df.empty:
        st.success("현재 Human Review 대상 항목이 없습니다.")
    else:
        render_table_with_csv(
            df=review_df[review_columns],
            filename="human_review.csv",
        )

        finding_map = {finding["finding_id"]: finding for finding in findings}

        selected_id = st.selectbox(
            "검토할 Finding 선택",
            review_df["finding_id"].tolist(),
            format_func=lambda value: format_finding_label(finding_map[value]),
            key="review_select",
        )

        finding = finding_map[selected_id]
        effective_review = get_effective_review_status(finding, saved_review_status)
        explanation = finding.get("agent_explanation", {})

        st.markdown("#### Review Detail")
        st.write(f"**현재 상태:** `{effective_review.get('current_status')}`")
        st.write(f"**권고:** {explanation.get('recommendation')}")
        st.write(f"**검토 사유:** {effective_review.get('review_reason')}")

        status_options = [
            "WAITING_HUMAN_REVIEW",
            "APPROVED_ROTATION",
            "FALSE_POSITIVE",
            "ACCEPTED_RISK",
            "RESOLVED",
        ]

        with st.form("review_decision_form"):
            selected_status = st.selectbox("Review 결정", status_options)
            reviewer = st.text_input("Reviewer", value="security_admin")
            note = st.text_area("Review Note", placeholder="검토 의견을 입력하세요.")

            submitted = st.form_submit_button("Save Review Decision")

        if submitted:
            save_review_decision(
                finding_id=selected_id,
                status=selected_status,
                reviewer=reviewer,
                note=note,
            )
            st.success("Review decision saved. Audit log updated.")
            st.rerun()

    with st.expander("설명", expanded=False):
        st.markdown(
            """
            이 영역은 **위험도가 높은 항목을 사람이 최종 확인하는 단계**입니다.

            자동화 시스템이 Secret 후보를 찾았다고 해서 바로 삭제하거나 권한을 회수하면 위험할 수 있습니다.  
            실제 Secret이 아닐 수도 있고, 이미 폐기된 값일 수도 있으며, 서비스 운영에 영향을 줄 수도 있습니다.

            그래서 이 시스템은 다음 방식으로 동작합니다.

            - Critical / High 항목을 우선 검토 대상으로 표시
            - 관리자가 검토 상태와 의견을 저장
            - 저장된 결정은 감사 로그에 기록
            - 실제 Secret 폐기나 권한 회수는 자동 수행하지 않음

            즉, 자동화는 빠르게 위험 후보를 찾아주고, 최종 판단은 사람이 책임 있게 내리도록 설계했습니다.
            """
        )

    close_story_section()


def render_audit_section(audit_df: pd.DataFrame) -> None:
    audit_count = len(audit_df)

    render_story_header(
        label="Audit Log",
        title=f"관리자 검토 결정이 {audit_count}건 기록되어 있습니다.",
        summary=(
            "검토자가 어떤 항목에 대해 어떤 결정을 했는지 기록합니다. "
            "이 기록은 사후 점검과 보안 감사에서 중요한 근거가 됩니다."
        ),
        accent="blue",
    )

    render_section_guide(
        title="검토 이력을 남겨 추적할 수 있게 합니다",
        paragraphs=[
            "보안 운영에서는 탐지 결과뿐 아니라 이후에 어떤 판단을 했는지도 중요합니다. 위험을 수용했는지, 오탐으로 판단했는지, 회전 조치를 승인했는지 기록이 남아야 합니다.",
            "이 영역은 검토자가 저장한 결정을 시간순으로 보여줍니다. 누가, 언제, 어떤 Finding에 대해 어떤 상태를 남겼는지 확인할 수 있습니다.",
            "현재 데모에서는 로컬 감사 로그 파일에 저장하지만, 실제 운영 환경에서는 SIEM, 티켓 시스템, 승인 워크플로우와 연결할 수 있습니다.",
        ],
    )

    if audit_df.empty:
        st.info("아직 저장된 감사 로그가 없습니다.")
    else:
        render_table_with_csv(
            df=audit_df,
            filename="audit_log.csv",
        )

    with st.expander("설명", expanded=False):
        st.markdown(
            """
            <div class="explain-note">
            Audit Log는 보안 조치의 추적 가능성을 보여주는 영역입니다.
            실제 운영 환경에서는 이 로그를 보안 감사, 사후 검토, 승인 이력 관리에 활용할 수 있습니다.
            </div>
            """,
            unsafe_allow_html=True,
        )

    close_story_section()


def render_raw_json_section(result: dict[str, Any]) -> None:
    render_story_header(
        label="Raw Output",
        title="대시보드의 모든 화면은 분석 결과 JSON을 기반으로 자동 생성됩니다.",
        summary=(
            "탐지 건수, 위험 등급, 정책 근거, 검토 상태는 하드코딩된 값이 아닙니다. "
            "분석 대상 폴더가 바뀌면 이 결과 파일도 함께 바뀌고, 화면도 자동으로 갱신됩니다."
        ),
        accent="yellow",
    )

    render_section_guide(
        title="분석 결과가 어떻게 저장되는지 확인합니다",
        paragraphs=[
            "이 영역은 대시보드가 읽고 있는 최종 결과 파일을 보여줍니다. 화면에 보이는 숫자와 표는 이 JSON 데이터를 기반으로 만들어집니다.",
            "분석 대상이 바뀌면 Secret 탐지 결과, 위험 점수, 정책 근거, 검토 상태도 함께 달라집니다. 즉, 특정 샘플에만 맞춘 정적인 화면이 아니라 입력 데이터에 따라 바뀌는 분석 대시보드입니다.",
            "개발 관점에서는 이 JSON이 Secret 탐지, 문맥 분석, 위험도 계산, 정책 근거, Agent 설명, 관리자 검토 결과를 모두 합친 최종 산출물입니다.",
        ],
    )

    st.json(result)

    with st.expander("설명", expanded=False):
        st.markdown(
            """
            <div class="explain-note">
            Raw JSON은 디버깅과 검증용입니다.
            Scanner Results, Risk Analysis, Policy Evidence, Human Review 화면은
            이 JSON의 필드를 읽어 자동으로 생성됩니다.
            </div>
            """,
            unsafe_allow_html=True,
        )

    close_story_section()


def render_story_header(label: str, title: str, summary: str, accent: str) -> None:
    st.markdown(
        f"""
        <div class="story-section accent-{accent}">
            <div class="section-label">{label}</div>
            <div class="big-result">{title}</div>
            <div class="section-summary">{summary}</div>
        """,
        unsafe_allow_html=True,
    )


def close_story_section() -> None:
    st.markdown("</div>", unsafe_allow_html=True)


def render_metric_row(metrics: list[tuple[str, Any]]) -> None:
    metric_html = '<div class="metric-row">'

    for label, value in metrics:
        metric_html += (
            '<div class="metric-card">'
            f'<div class="metric-label">{label}</div>'
            f'<div class="metric-value">{value}</div>'
            "</div>"
        )

    metric_html += "</div>"

    st.markdown(metric_html, unsafe_allow_html=True)


def render_section_guide(title: str, paragraphs: list[str]) -> None:
    paragraph_html = ""

    for paragraph in paragraphs:
        paragraph_html += f"<p>{paragraph}</p>"

    st.markdown(
        f"""
        <div class="section-note">
            <strong>{title}</strong>
            {paragraph_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_table_with_csv(df: pd.DataFrame, filename: str) -> None:
    st.markdown("#### 상세 데이터")
    st.dataframe(df, use_container_width=True, hide_index=True)

    csv_data = df.to_csv(index=False).encode("utf-8-sig")

    st.download_button(
        label="CSV 다운로드",
        data=csv_data,
        file_name=filename,
        mime="text/csv",
        key=f"download_{filename}",
    )


def build_findings_dataframe(
    findings: list[dict[str, Any]],
    saved_review_status: dict[str, dict[str, Any]],
) -> pd.DataFrame:
    rows = []

    for finding in findings:
        context = finding.get("context", {})
        effective_review = get_effective_review_status(finding, saved_review_status)

        rows.append(
            {
                "finding_id": finding.get("finding_id"),
                "detector": finding.get("detector", "unknown"),
                "secret_type": finding.get("secret_type"),
                "file_path": finding.get("file_path"),
                "line_number": finding.get("line_number"),
                "line_content": finding.get("line_content", ""),
                "masked_secret": finding.get("masked_secret"),
                "occurrence_count": finding.get("occurrence_count", 1),
                "risk_score": finding.get("risk_score"),
                "risk_level": finding.get("risk_level"),
                "requires_human_review": finding.get("requires_human_review"),
                "review_status": effective_review.get("current_status"),
                "reviewer": effective_review.get("reviewer"),
                "reviewed_at": effective_review.get("reviewed_at"),
                "file_type": context.get("file_type"),
                "environment_hint": context.get("environment_hint"),
                "file_criticality": context.get("file_criticality"),
                "context_keywords": ", ".join(context.get("context_keywords", [])),
            }
        )

    return pd.DataFrame(rows)


def build_risk_dataframe(findings: list[dict[str, Any]]) -> pd.DataFrame:
    rows = []

    for finding in findings:
        score_detail = finding.get("score_detail", {})

        rows.append(
            {
                "finding_id": finding.get("finding_id"),
                "secret_type": finding.get("secret_type"),
                "detector": finding.get("detector"),
                "file_path": finding.get("file_path"),
                "occurrence_count": finding.get("occurrence_count", 1),
                "type_risk": score_detail.get("type_risk"),
                "exposure_risk": score_detail.get("exposure_risk"),
                "base_score": score_detail.get("base_score"),
                "context_bonus": score_detail.get("context_bonus"),
                "file_criticality_bonus": score_detail.get("file_criticality_bonus"),
                "frequency_bonus": score_detail.get("frequency_bonus"),
                "risk_score": finding.get("risk_score"),
                "risk_level": finding.get("risk_level"),
            }
        )

    return pd.DataFrame(rows).sort_values(by="risk_score", ascending=False)


def build_policy_dataframe(findings: list[dict[str, Any]]) -> pd.DataFrame:
    rows = []

    for finding in findings:
        policy_evidence = finding.get("policy_evidence", {})
        matched_policies = policy_evidence.get("matched_policies", [])

        if not matched_policies:
            rows.append(
                {
                    "finding_id": finding.get("finding_id"),
                    "secret_type": finding.get("secret_type"),
                    "risk_level": finding.get("risk_level"),
                    "matched_policy_count": 0,
                    "policy_id": "",
                    "policy_title": "",
                    "summary": "",
                }
            )
            continue

        for policy in matched_policies:
            rows.append(
                {
                    "finding_id": finding.get("finding_id"),
                    "secret_type": finding.get("secret_type"),
                    "risk_level": finding.get("risk_level"),
                    "matched_policy_count": len(matched_policies),
                    "policy_id": policy.get("policy_id"),
                    "policy_title": policy.get("title"),
                    "summary": policy.get("summary"),
                }
            )

    return pd.DataFrame(rows)


def build_audit_dataframe() -> pd.DataFrame:
    logs = read_audit_logs()

    if not logs:
        return pd.DataFrame()

    return pd.DataFrame(logs)


def format_detector_result(regex_count: int, entropy_count: int) -> str:
    if regex_count and entropy_count:
        return f"정규식 {regex_count}건, 엔트로피 {entropy_count}건으로 Secret 후보를 탐지했습니다."

    if regex_count:
        return f"정규식 기반으로 Secret 후보 {regex_count}건을 탐지했습니다."

    if entropy_count:
        return f"엔트로피 기반으로 Secret 후보 {entropy_count}건을 탐지했습니다."

    return "탐지된 Secret 후보가 없습니다."


def get_top_risk_finding(findings: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not findings:
        return None

    return max(findings, key=lambda item: item.get("risk_score", 0))


def format_finding_label(finding: dict[str, Any]) -> str:
    return (
        f"{finding.get('finding_id')} | "
        f"{finding.get('risk_level')} | "
        f"{finding.get('secret_type')} | "
        f"{finding.get('file_path')}"
    )


if __name__ == "__main__":
    main()
