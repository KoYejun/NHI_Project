import json
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

REPORT_PATH = Path("reports/result.json")


def main() -> None:
    st.set_page_config(
        page_title="NHI Secret Agent Dashboard",
        page_icon="🛡️",
        layout="wide",
    )

    st.title("NHI Secret Agent Dashboard")
    st.caption("Secret 탐지 결과, 위험도, 정책 근거, Human Review 대상을 확인하는 관리자용 대시보드")

    if not REPORT_PATH.exists():
        st.warning("reports/result.json 파일이 없습니다.")
        st.code("python scripts/create_sample_project.py\npython -m app.main --target-path data/sample_project")
        return

    result = load_result(REPORT_PATH)
    summary = result.get("summary", {})
    findings = result.get("findings", [])

    if not findings:
        st.info("탐지 결과가 없습니다.")
        return

    findings_df = build_findings_dataframe(findings)

    render_summary(summary)
    render_charts(findings_df)

    tab_overview, tab_detail, tab_review, tab_policy, tab_raw = st.tabs(
        [
            "Finding Overview",
            "Finding Detail",
            "Human Review",
            "Policy Evidence",
            "Raw JSON",
        ]
    )

    with tab_overview:
        render_finding_overview(findings_df)

    with tab_detail:
        render_finding_detail(findings)

    with tab_review:
        render_human_review(findings_df, findings)

    with tab_policy:
        render_policy_evidence(findings)

    with tab_raw:
        render_raw_json(result)


def load_result(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_findings_dataframe(findings: list[dict[str, Any]]) -> pd.DataFrame:
    rows = []

    for finding in findings:
        context = finding.get("context", {})

        rows.append(
            {
                "finding_id": finding.get("finding_id"),
                "secret_type": finding.get("secret_type"),
                "file_path": finding.get("file_path"),
                "line_number": finding.get("line_number"),
                "risk_score": finding.get("risk_score"),
                "risk_level": finding.get("risk_level"),
                "requires_human_review": finding.get("requires_human_review"),
                "file_type": context.get("file_type"),
                "environment_hint": context.get("environment_hint"),
                "file_criticality": context.get("file_criticality"),
            }
        )

    return pd.DataFrame(rows)


def render_summary(summary: dict[str, Any]) -> None:
    st.subheader("Summary")

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("Total Findings", summary.get("total", 0))
    col2.metric("Critical", summary.get("Critical", 0))
    col3.metric("High", summary.get("High", 0))
    col4.metric("Medium", summary.get("Medium", 0))
    col5.metric("Human Review", summary.get("human_review_required", 0))


def render_charts(findings_df: pd.DataFrame) -> None:
    st.subheader("Risk Distribution")

    col1, col2 = st.columns(2)

    with col1:
        risk_order = ["Critical", "High", "Medium", "Low"]
        risk_counts = findings_df["risk_level"].value_counts().reindex(risk_order, fill_value=0)
        st.write("위험 등급별 탐지 건수")
        st.bar_chart(risk_counts)

    with col2:
        type_counts = findings_df["secret_type"].value_counts()
        st.write("Secret 유형별 탐지 건수")
        st.bar_chart(type_counts)


def render_finding_overview(findings_df: pd.DataFrame) -> None:
    st.subheader("Finding Overview")

    risk_levels = ["All"] + sorted(findings_df["risk_level"].dropna().unique().tolist())
    selected_level = st.selectbox("위험 등급 필터", risk_levels)

    filtered_df = findings_df

    if selected_level != "All":
        filtered_df = findings_df[findings_df["risk_level"] == selected_level]

    st.dataframe(
        filtered_df,
        use_container_width=True,
        hide_index=True,
    )


def render_finding_detail(findings: list[dict[str, Any]]) -> None:
    st.subheader("Finding Detail")

    finding_map = {finding["finding_id"]: finding for finding in findings}
    finding_ids = list(finding_map.keys())

    selected_id = st.selectbox(
        "상세 확인할 Finding 선택",
        finding_ids,
        format_func=lambda value: format_finding_label(finding_map[value]),
    )

    finding = finding_map[selected_id]
    context = finding.get("context", {})
    score_detail = finding.get("score_detail", {})
    explanation = finding.get("agent_explanation", {})

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("### 기본 정보")
        st.write(f"**Finding ID:** {finding.get('finding_id')}")
        st.write(f"**Secret Type:** {finding.get('secret_type')}")
        st.write(f"**File Path:** `{finding.get('file_path')}`")
        st.write(f"**Line Number:** {finding.get('line_number')}")
        st.write(f"**Masked Secret:** `{finding.get('masked_secret')}`")
        st.write(f"**Risk Level:** {finding.get('risk_level')}")
        st.write(f"**Risk Score:** {finding.get('risk_score')}")
        st.write(f"**Human Review:** {finding.get('requires_human_review')}")

    with col2:
        st.markdown("### 점수 산정 근거")
        st.write(f"**TypeRisk:** {score_detail.get('type_risk')}")
        st.write(f"**ExposureRisk:** {score_detail.get('exposure_risk')}")
        st.write(f"**ContextBonus:** {score_detail.get('context_bonus')}")
        st.write(f"**FileCriticalityBonus:** {score_detail.get('file_criticality_bonus')}")
        st.write(f"**FrequencyBonus:** {score_detail.get('frequency_bonus')}")

    st.markdown("### 문맥 분석")
    st.write(f"**파일 유형:** {context.get('file_type')}")
    st.write(f"**환경 단서:** {context.get('environment_hint')}")
    st.write(f"**파일 중요도:** {context.get('file_criticality')}")
    st.write(f"**문맥 키워드:** {', '.join(context.get('context_keywords', []))}")
    st.info(context.get("context_summary", ""))

    st.markdown("### Agent 분석")
    st.write(f"**탐지 요약:** {explanation.get('summary')}")
    st.write(f"**위험 판단:** {explanation.get('risk_reason')}")
    st.write(f"**NHI 연결 가능성:** {explanation.get('nhi_possibility')}")
    st.write(f"**가능한 영향:** {explanation.get('possible_impact')}")
    st.write(f"**정책 근거 요약:** {explanation.get('policy_basis')}")
    st.write(f"**대응 권고:** {explanation.get('recommendation')}")
    st.write(f"**사람 검토:** {explanation.get('human_review')}")


def render_human_review(findings_df: pd.DataFrame, findings: list[dict[str, Any]]) -> None:
    st.subheader("Human Review Queue")

    review_df = findings_df[findings_df["requires_human_review"]]

    if review_df.empty:
        st.success("현재 Human Review 대상 항목이 없습니다.")
        return

    st.dataframe(
        review_df,
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("### Review Reasons")

    finding_map = {finding["finding_id"]: finding for finding in findings}

    for finding_id in review_df["finding_id"].tolist():
        finding = finding_map[finding_id]
        explanation = finding.get("agent_explanation", {})

        with st.expander(format_finding_label(finding)):
            st.write(explanation.get("human_review"))
            st.write(explanation.get("recommendation"))


def render_policy_evidence(findings: list[dict[str, Any]]) -> None:
    st.subheader("Policy Evidence")

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


def render_raw_json(result: dict[str, Any]) -> None:
    st.subheader("Raw JSON")
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
