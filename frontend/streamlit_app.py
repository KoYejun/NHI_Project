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


def main() -> None:
    st.set_page_config(
        page_title="NHI Secret Agent Dashboard",
        page_icon="🛡️",
        layout="wide",
    )

    apply_styles()

    st.title("NHI Secret Agent Dashboard")
    st.caption(
        "개발1 Secret Discovery & Risk Analysis 기능과 "
        "개발2 LangGraph Agent & Reporting 기능을 통합한 완전판 대시보드"
    )

    render_sidebar()
    render_flow_cards()

    result = load_result_if_exists()

    if result is None:
        st.info(
            "아직 분석 결과가 없습니다. "
            "왼쪽 사이드바에서 `Create Sample Project`를 누른 뒤 `Run Analysis`를 실행하세요."
        )
        render_empty_guide()
        return

    findings = result.get("findings", [])
    summary = result.get("summary", {})
    saved_review_status = load_review_status()

    if not findings:
        st.warning("분석 결과 파일은 있지만 Finding이 없습니다.")
        st.json(result)
        return

    findings_df = build_findings_dataframe(findings, saved_review_status)

    render_summary(summary, findings_df)

    (
        tab_pipeline,
        tab_scanner,
        tab_risk,
        tab_detail,
        tab_policy,
        tab_review,
        tab_audit,
        tab_raw,
    ) = st.tabs(
        [
            "Pipeline Overview",
            "Scanner Results",
            "Risk Analysis",
            "Finding Detail",
            "Policy Evidence",
            "Review Workflow",
            "Audit Log",
            "Raw JSON",
        ]
    )

    with tab_pipeline:
        render_pipeline_tab(findings_df)

    with tab_scanner:
        render_scanner_results(findings_df)

    with tab_risk:
        render_risk_analysis(findings)

    with tab_detail:
        render_finding_detail(findings, saved_review_status)

    with tab_policy:
        render_policy_evidence(findings)

    with tab_review:
        render_review_workflow(findings, findings_df, saved_review_status)

    with tab_audit:
        render_audit_log()

    with tab_raw:
        render_raw_json(result)


def apply_styles() -> None:
    st.markdown(
        """
        <style>
        .step-card {
            border: 1px solid #e7e7e7;
            border-radius: 14px;
            padding: 16px 18px;
            margin-bottom: 12px;
            background-color: #fafafa;
            min-height: 132px;
        }
        .step-title {
            font-weight: 700;
            font-size: 16px;
            margin-bottom: 8px;
        }
        .step-owner {
            display: inline-block;
            font-size: 12px;
            padding: 3px 8px;
            border-radius: 999px;
            background-color: #eeeeee;
            margin-bottom: 8px;
        }
        .step-desc {
            color: #555;
            font-size: 14px;
            line-height: 1.45;
        }
        .small-muted {
            color: #666;
            font-size: 13px;
            line-height: 1.45;
        }
        .section-note {
            border-left: 4px solid #d0d0d0;
            padding: 8px 12px;
            background-color: #fafafa;
            color: #444;
            font-size: 14px;
            margin-bottom: 14px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar() -> None:
    st.sidebar.header("Analysis Control")

    target_path = st.sidebar.text_input(
        "분석 대상 폴더",
        value="data/sample_project",
        help="개발1 호환 Scanner Engine이 스캔할 폴더 경로입니다.",
    )

    st.sidebar.markdown("### 실행 순서")
    st.sidebar.markdown(
        """
        1. 샘플 프로젝트 생성  
        2. 전체 분석 실행  
        3. Scanner / Risk 결과 확인  
        4. Review Workflow에서 검토 결정 저장  
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
    st.sidebar.markdown("### Generated Files")
    st.sidebar.code(
        "reports/raw_findings.json\n"
        "reports/risk_results.json\n"
        "reports/result.json\n"
        "reports/report.md\n"
        "reports/review_status.json\n"
        "reports/audit_log.jsonl"
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("### CLI 실행")
    st.sidebar.code(
        "python scripts/create_sample_project.py\n"
        "python -m app.main --target-path data/sample_project"
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
        st.sidebar.info("먼저 `Create Sample Project` 버튼을 눌러 샘플 프로젝트를 생성하세요.")
        return

    with st.spinner("개발1 Scanner Engine과 개발2 LangGraph Agent를 실행하는 중입니다..."):
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

    st.sidebar.success(
        f"분석 완료: "
        f"Findings {len(final_state['raw_findings'])}건, "
        f"Errors {len(final_state['errors'])}건"
    )
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


def render_flow_cards() -> None:
    st.subheader("전체 분석 흐름")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        step_card(
            title="1. Discovery",
            owner="개발1",
            description="정규식 탐지와 엔트로피 탐지로 Secret 후보를 찾고 원문을 마스킹합니다.",
        )

    with col2:
        step_card(
            title="2. Risk Scoring",
            owner="개발1",
            description="파일 위치, 환경 단서, 문맥 키워드, 반복 노출 횟수를 반영해 위험 점수를 계산합니다.",
        )

    with col3:
        step_card(
            title="3. Agent Analysis",
            owner="개발2",
            description="정책 근거를 연결하고, 보안 담당자가 이해할 수 있는 Agent 설명을 생성합니다.",
        )

    with col4:
        step_card(
            title="4. Human Review",
            owner="개발2",
            description="Critical / High 항목을 관리자 검토 대상으로 분류하고 검토 이력을 남깁니다.",
        )


def step_card(title: str, owner: str, description: str) -> None:
    st.markdown(
        f"""
        <div class="step-card">
            <div class="step-owner">{owner}</div>
            <div class="step-title">{title}</div>
            <div class="step-desc">{description}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_empty_guide() -> None:
    st.markdown("### 처음 실행하는 경우")

    st.markdown(
        """
        ```text
        1. 왼쪽 사이드바에서 Create Sample Project 클릭
        2. Run Analysis 클릭
        3. Summary와 각 탭에서 결과 확인
        ```
        """
    )

    st.markdown("### 터미널에서 직접 실행하려면")

    st.code(
        "python scripts/create_sample_project.py\n"
        "python -m app.main --target-path data/sample_project\n"
        "streamlit run frontend/streamlit_app.py",
        language="powershell",
    )


def render_summary(summary: dict[str, Any], findings_df: pd.DataFrame) -> None:
    st.subheader("Summary")

    regex_count = int((findings_df["detector"] == "regex").sum())
    entropy_count = int((findings_df["detector"] == "entropy").sum())
    pending_count = int((findings_df["review_status"] == "WAITING_HUMAN_REVIEW").sum())
    reviewed_count = int(
        findings_df["review_status"]
        .isin(["APPROVED_ROTATION", "FALSE_POSITIVE", "ACCEPTED_RISK", "RESOLVED"])
        .sum()
    )

    col1, col2, col3, col4, col5, col6, col7 = st.columns(7)

    col1.metric("Total", summary.get("total", len(findings_df)))
    col2.metric("Critical", summary.get("Critical", 0))
    col3.metric("High", summary.get("High", 0))
    col4.metric("Regex", regex_count)
    col5.metric("Entropy", entropy_count)
    col6.metric("Pending", pending_count)
    col7.metric("Reviewed", reviewed_count)

    st.markdown(
        """
        <div class="section-note">
        Total은 전체 탐지 건수, Regex/Entropy는 탐지 방식별 건수,
        Pending은 아직 관리자 검토가 필요한 항목 수입니다.
        </div>
        """,
        unsafe_allow_html=True,
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


def render_pipeline_tab(findings_df: pd.DataFrame) -> None:
    st.subheader("Pipeline Overview")

    st.markdown(
        """
        이 탭은 개발1과 개발2 기능이 하나의 흐름으로 어떻게 연결되는지 보여줍니다.

        - 개발1: Secret 탐지, 마스킹, fingerprint, 문맥 분석, 위험도 계산
        - 개발2: 정책 근거, Agent 설명, Human Review, 리포트, 대시보드
        """
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.write("위험 등급별 분포")
        risk_order = ["Critical", "High", "Medium", "Low"]
        risk_counts = findings_df["risk_level"].value_counts().reindex(risk_order, fill_value=0)
        st.bar_chart(risk_counts)

    with col2:
        st.write("탐지 방식별 분포")
        detector_counts = findings_df["detector"].value_counts()
        st.bar_chart(detector_counts)

    with col3:
        st.write("Review 상태별 분포")
        review_counts = findings_df["review_status"].value_counts()
        st.bar_chart(review_counts)

    st.markdown("### 전체 Finding 테이블")
    overview_columns = [
        "finding_id",
        "detector",
        "secret_type",
        "file_path",
        "risk_score",
        "risk_level",
        "review_status",
    ]

    st.dataframe(
        findings_df[overview_columns],
        use_container_width=True,
        hide_index=True,
    )


def render_scanner_results(findings_df: pd.DataFrame) -> None:
    st.subheader("Scanner Results")

    st.markdown(
        """
        개발1 호환 Scanner Engine의 탐지 결과입니다.

        - `regex`: AWS Key, GitHub Token, Slack Token, Bearer Token, Generic API Key 등 정규식 기반 탐지
        - `entropy`: 정규식으로 잡기 어려운 고엔트로피 문자열 탐지
        """
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        detector_filter = st.selectbox(
            "탐지 방식",
            ["All"] + sorted(findings_df["detector"].dropna().unique().tolist()),
        )

    with col2:
        secret_type_filter = st.selectbox(
            "Secret 유형",
            ["All"] + sorted(findings_df["secret_type"].dropna().unique().tolist()),
        )

    with col3:
        risk_level_filter = st.selectbox(
            "위험 등급",
            ["All"] + sorted(findings_df["risk_level"].dropna().unique().tolist()),
        )

    filtered_df = findings_df.copy()

    if detector_filter != "All":
        filtered_df = filtered_df[filtered_df["detector"] == detector_filter]

    if secret_type_filter != "All":
        filtered_df = filtered_df[filtered_df["secret_type"] == secret_type_filter]

    if risk_level_filter != "All":
        filtered_df = filtered_df[filtered_df["risk_level"] == risk_level_filter]

    scanner_columns = [
        "finding_id",
        "detector",
        "secret_type",
        "file_path",
        "line_number",
        "masked_secret",
        "occurrence_count",
        "risk_level",
        "line_content",
    ]

    st.dataframe(
        filtered_df[scanner_columns],
        use_container_width=True,
        hide_index=True,
    )


def render_risk_analysis(findings: list[dict[str, Any]]) -> None:
    st.subheader("Risk Analysis")

    st.markdown(
        """
        개발1 위험도 산식의 상세 계산 결과입니다.

        ```text
        SecretRisk = TypeRisk × ExposureRisk
                     + ContextBonus
                     + FileCriticalityBonus
                     + FrequencyBonus
        ```
        """
    )

    risk_rows = []

    for finding in findings:
        score_detail = finding.get("score_detail", {})

        risk_rows.append(
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

    risk_df = pd.DataFrame(risk_rows).sort_values(
        by="risk_score",
        ascending=False,
    )

    st.dataframe(
        risk_df,
        use_container_width=True,
        hide_index=True,
    )

    finding_map = {finding["finding_id"]: finding for finding in findings}

    selected_id = st.selectbox(
        "점수 산정 상세 확인",
        list(finding_map.keys()),
        format_func=lambda value: format_finding_label(finding_map[value]),
        key="risk_detail_select",
    )

    selected_finding = finding_map[selected_id]
    score_detail = selected_finding.get("score_detail", {})

    col1, col2, col3 = st.columns(3)

    col1.metric("Final Score", selected_finding.get("risk_score"))
    col2.metric("Risk Level", selected_finding.get("risk_level"))
    col3.metric("Occurrence", selected_finding.get("occurrence_count", 1))

    st.markdown("### 점수 구성")
    st.write(f"- TypeRisk: `{score_detail.get('type_risk')}`")
    st.write(f"- ExposureRisk: `{score_detail.get('exposure_risk')}`")
    st.write(f"- BaseScore: `{score_detail.get('base_score')}`")
    st.write(f"- ContextBonus: `{score_detail.get('context_bonus')}`")
    st.write(f"- FileCriticalityBonus: `{score_detail.get('file_criticality_bonus')}`")
    st.write(f"- FrequencyBonus: `{score_detail.get('frequency_bonus')}`")

    st.markdown("### 해석")
    st.info(
        "위험 점수는 Secret 유형 자체의 위험도뿐 아니라, "
        "노출 위치, 운영 환경 문맥, 파일 중요도, 반복 노출 횟수를 함께 반영합니다."
    )


def render_finding_detail(
    findings: list[dict[str, Any]],
    saved_review_status: dict[str, dict[str, Any]],
) -> None:
    st.subheader("Finding Detail")

    finding_map = {finding["finding_id"]: finding for finding in findings}

    selected_id = st.selectbox(
        "상세 확인할 Finding 선택",
        list(finding_map.keys()),
        format_func=lambda value: format_finding_label(finding_map[value]),
        key="finding_detail_select",
    )

    finding = finding_map[selected_id]
    context = finding.get("context", {})
    score_detail = finding.get("score_detail", {})
    explanation = finding.get("agent_explanation", {})
    effective_review = get_effective_review_status(finding, saved_review_status)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 기본 정보")
        st.write(f"**Finding ID:** `{finding.get('finding_id')}`")
        st.write(f"**Detector:** `{finding.get('detector')}`")
        st.write(f"**Secret Type:** `{finding.get('secret_type')}`")
        st.write(f"**File Path:** `{finding.get('file_path')}`")
        st.write(f"**Line Number:** `{finding.get('line_number')}`")
        st.write(f"**Masked Secret:** `{finding.get('masked_secret')}`")
        st.write(f"**Occurrence Count:** `{finding.get('occurrence_count', 1)}`")
        st.write(f"**Risk:** `{finding.get('risk_level')}` / `{finding.get('risk_score')}`")

    with col2:
        st.markdown("### Review 상태")
        st.write(f"**Current Status:** `{effective_review.get('current_status')}`")
        st.write(f"**Required Reviewer:** `{effective_review.get('required_reviewer')}`")
        st.write(f"**Reviewer:** `{effective_review.get('reviewer')}`")
        st.write(f"**Reviewed At:** `{effective_review.get('reviewed_at')}`")
        st.write(f"**Source:** `{effective_review.get('source')}`")

    st.markdown("### 탐지 라인")
    st.code(finding.get("line_content", ""), language="text")

    st.markdown("### 점수 산정 근거")
    st.write(f"- TypeRisk: `{score_detail.get('type_risk')}`")
    st.write(f"- ExposureRisk: `{score_detail.get('exposure_risk')}`")
    st.write(f"- BaseScore: `{score_detail.get('base_score')}`")
    st.write(f"- ContextBonus: `{score_detail.get('context_bonus')}`")
    st.write(f"- FileCriticalityBonus: `{score_detail.get('file_criticality_bonus')}`")
    st.write(f"- FrequencyBonus: `{score_detail.get('frequency_bonus')}`")

    st.markdown("### 문맥 분석")
    st.write(f"**파일 유형:** `{context.get('file_type')}`")
    st.write(f"**환경 단서:** `{context.get('environment_hint')}`")
    st.write(f"**파일 중요도:** `{context.get('file_criticality')}`")
    st.write(f"**문맥 키워드:** `{', '.join(context.get('context_keywords', []))}`")
    st.info(context.get("context_summary", ""))

    st.markdown("### Agent 분석")
    st.write(f"**탐지 요약:** {explanation.get('summary')}")
    st.write(f"**위험 판단:** {explanation.get('risk_reason')}")
    st.write(f"**NHI 연결 가능성:** {explanation.get('nhi_possibility')}")
    st.write(f"**가능한 영향:** {explanation.get('possible_impact')}")
    st.write(f"**정책 근거 요약:** {explanation.get('policy_basis')}")
    st.write(f"**대응 권고:** {explanation.get('recommendation')}")
    st.write(f"**사람 검토:** {explanation.get('human_review')}")


def render_policy_evidence(findings: list[dict[str, Any]]) -> None:
    st.subheader("Policy Evidence")

    st.markdown(
        """
        탐지 결과와 연결된 로컬 정책 문서 근거입니다.  
        이 탭은 개발2의 Policy Evidence 기능을 보여줍니다.
        """
    )

    for finding in findings:
        policy_evidence = finding.get("policy_evidence", {})
        matched_policies = policy_evidence.get("matched_policies", [])

        with st.expander(format_finding_label(finding)):
            if not matched_policies:
                st.warning("연결된 정책 근거가 없습니다.")
                continue

            for policy in matched_policies:
                st.markdown(f"**{policy.get('title')}**")
                st.write(f"- Policy ID: `{policy.get('policy_id')}`")
                st.write(f"- Relevance Score: `{policy.get('relevance_score')}`")
                st.write(f"- Summary: {policy.get('summary')}")


def render_review_workflow(
    findings: list[dict[str, Any]],
    findings_df: pd.DataFrame,
    saved_review_status: dict[str, dict[str, Any]],
) -> None:
    st.subheader("Review Workflow")

    st.markdown(
        """
        Critical / High 항목은 자동 조치하지 않고 관리자 검토 대상으로 분류합니다.  
        저장한 결정은 `review_status.json`과 `audit_log.jsonl`에 기록됩니다.
        """
    )

    review_df = findings_df[findings_df["requires_human_review"]]

    if review_df.empty:
        st.success("현재 Human Review 대상 항목이 없습니다.")
        return

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

    st.dataframe(
        review_df[review_columns],
        use_container_width=True,
        hide_index=True,
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

    st.markdown("### Review Detail")
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


def render_audit_log() -> None:
    st.subheader("Audit Log")

    st.markdown(
        """
        Review Workflow에서 저장한 검토 결정 이력을 보여줍니다.  
        실제 Secret 폐기나 권한 회수는 수행하지 않고, 검토 상태와 감사 증적만 남깁니다.
        """
    )

    logs = read_audit_logs()

    if not logs:
        st.info("아직 저장된 감사 로그가 없습니다.")
        return

    st.dataframe(
        pd.DataFrame(logs),
        use_container_width=True,
        hide_index=True,
    )


def render_raw_json(result: dict[str, Any]) -> None:
    st.subheader("Raw JSON")

    st.markdown("대시보드가 사용하는 최종 `reports/result.json` 원본입니다.")

    st.json(result)


def format_finding_label(finding: dict[str, Any]) -> str:
    return (
        f"{finding.get('finding_id')} | "
        f"{finding.get('risk_level')} | "
        f"{finding.get('secret_type')} | "
        f"{finding.get('file_path')}"
    )


if __name__ == "__main__":
    main()