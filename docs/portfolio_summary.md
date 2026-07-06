# 포트폴리오 요약: NHI Secret 위험 분석 및 리포팅 Agent

## 프로젝트명

LangGraph 기반 NHI Secret 위험 분석 및 리포팅 Agent MVP

## 프로젝트 목적

소스코드, 설정 파일, 로그 등에 노출될 수 있는 NHI Secret 후보를 탐지하고,
문맥 분석과 위험도 점수화를 통해 관리자 검토 가능한 리포트를 생성하는 보안 Agent를 구현했다.

## 본인 담당 역할

LangGraph Agent & Reporting 담당

## 담당 구현 내용

- AgentState 설계
- LangGraph Workflow 구성
- Discovery, Context Analysis, Risk Scoring, Explanation, Report Node 연결
- 로컬 샘플 폴더 기반 Secret Scanner Adapter 구현
- 규칙 기반 Explanation Agent 구현
- JSON/Markdown 리포트 생성
- Secret 원문 미저장 및 마스킹 처리
- pytest 기반 보안성 검증
- 공개 저장소용 샘플 프로젝트 생성 스크립트 작성

## 핵심 기술

- Python
- LangGraph
- Typer
- pytest
- Ruff
- Markdown Report
- JSON Report

## 개인정보보호
Secret 자체가 개인정보는 아니지만, Secret은 개인정보처리시스템, DB, SaaS, API에 접근할 수 있는 인증수단이 될 수 있다.
따라서 Secret 노출은 개인정보 접근권한 노출 위험으로 이어질 수 있다.

본 프로젝트에서는 탐지된 Secret 후보에 대해 NHI 연결 가능성, 가능한 영향, 대응 권고, Human Review 여부를 리포트에 포함해
개인정보보호 관점의 접근권한 관리와 검토 증적 확보를 고려했다.

## 주요 성과

- 로컬 샘플 폴더를 입력하면 Secret 후보를 자동 탐지
- Secret 원문을 저장하지 않고 마스킹된 값만 리포트에 포함
- 위험 점수와 Critical/High/Medium/Low 등급 산정
- Critical/High 항목은 Human Review 대상으로 분류
- result.json과 report.md 자동 생성
- 테스트를 통해 Secret 원문 미포함 여부 검증

## 한계 및 향후 계획

현재는 로컬 샘플 폴더 기반 MVP이며, 실제 GitHub/AWS/Slack API와는 연동하지 않았다.
향후 정책 문서 RAG, Streamlit 대시보드, NetworkX 기반 Blast Radius 분석, Human Approval 상태 관리로 확장할 수 있다.