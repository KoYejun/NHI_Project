# Portfolio Summary

## 프로젝트명

NHI Secret Agent  
LangGraph 기반 NHI Secret 위험 분석 및 관리자 검토 리포팅 시스템

## 프로젝트 유형

```text
보안 자동화
클라우드 접근권한 관리
NHI Secret 탐지
개인정보보호 접근통제
보안 운영 대시보드
```

## 프로젝트 목표

소스코드, 설정 파일, 로그에 노출될 수 있는 NHI Secret 후보를 탐지하고, 이를 위험도 분석, 정책 근거, 관리자 검토, 감사 로그까지 연결하는 보안 운영형 Agent MVP를 구현했다.

## 핵심 문제의식

Secret은 단순 문자열이 아니라 시스템 접근권한과 연결된 인증수단이다.  
특히 NHI Secret이 노출되면 클라우드 리소스, 저장소, 외부 API, 개인정보처리시스템 접근권한이 함께 노출될 수 있다.

따라서 Secret 탐지 결과는 단순 목록이 아니라 다음 정보와 함께 제공되어야 한다.

```text
위험도
문맥
정책 근거
대응 권고
관리자 검토 필요 여부
감사 로그
```

## 본인 담당 역할

LangGraph Agent & Reporting 담당

## 담당 구현 내용

```text
AgentState 설계
LangGraph Workflow 구성
Local Secret Scanner Adapter 구현
Secret 마스킹 처리
Context Analysis Node 구현
Risk Scoring Node 연결
Policy Evidence Node 구현
Explanation Node 구현
Human Review Node 구현
Report Node 구현
Streamlit Dashboard 구현
Review 상태 저장 기능 구현
Audit Log 기록 기능 구현
pytest 테스트 작성
Ruff 코드 품질 검증 구성
Quality Gate 스크립트 작성
GitHub Actions CI 구성
```

## 기술 스택

```text
Python
LangGraph
Typer
Streamlit
Pandas
pytest
Ruff
Markdown
JSON
JSONL
GitHub Actions
```

## 시스템 흐름

```text
Sample Project
→ Secret Scanner
→ Context Analysis
→ Risk Scoring
→ Policy Evidence
→ Explanation Agent
→ Human Review
→ Report Generator
→ Streamlit Dashboard
→ Audit Log
```

## 주요 기능

```text
1. 로컬 폴더 기반 Secret 후보 탐지
2. Secret 원문 미저장 및 마스킹
3. 파일 유형과 환경 단서 기반 문맥 분석
4. 위험도 점수화 및 등급 분류
5. 정책 문서 기반 RAG-lite 근거 검색
6. 관리자용 Agent 설명 생성
7. Critical / High 항목 Human Review Queue 분류
8. Review 결정 상태 저장
9. JSONL 기반 Audit Log 기록
10. JSON / Markdown 리포트 생성
11. Streamlit 관리자 대시보드 제공
12. pytest / Ruff / Quality Gate 기반 검증
```

## 개인정보보호와의 연결성

Secret 자체가 개인정보는 아니지만, Secret은 개인정보처리시스템, DB, 클라우드 리소스, 외부 API에 접근할 수 있는 인증수단이 될 수 있다.

따라서 Secret 노출은 개인정보 접근권한 노출 위험으로 이어질 수 있다.

본 프로젝트는 다음 개인정보보호 실무 영역과 연결된다.

```text
개인정보처리시스템 접근통제
최소권한 원칙
비인가 접근 위험 관리
사고 대응 절차
관리자 승인 및 검토
감사 로그와 증적 관리
```

## 보안 설계 포인트

```text
1. Secret 원문을 저장하지 않음
2. 마스킹된 값만 리포트에 포함
3. 외부 LLM API 미사용
4. 실제 Secret 유효성 검증 미수행
5. 실제 권한 회수 미수행
6. Human Review 기반 검토 구조
7. Audit Log 기반 증적 관리
8. Quality Gate로 공개 전 보안 점검 자동화
```

## 성과

```text
탐지 → 분석 → 정책 근거 → 관리자 검토 → 감사 로그까지 이어지는 보안 운영 흐름 구현
LangGraph 기반으로 Node 단위 확장 가능한 구조 설계
Streamlit 대시보드로 결과 확인성과 발표 효과 확보
Secret 원문 미저장 원칙을 테스트와 Quality Gate로 검증
정책 근거 기반 리포팅을 통해 개인정보보호 직무와 연결 가능한 포트폴리오 완성
```

## 한계

```text
실제 GitHub / AWS / Slack API와 연동하지 않음
실제 Secret 유효성 검증 미수행
실제 권한 회수나 폐기 미수행
정책 검색은 keyword 기반 RAG-lite 방식
Review 상태는 로컬 JSON 파일 기반
```

## 향후 확장

```text
GitHub Repository Clone 기반 스캔
AWS IAM 권한 범위 분석
NetworkX 기반 Blast Radius 분석
벡터DB 기반 정책 RAG
티켓 시스템 연동
조직 승인 워크플로 연동
CI/CD Secret Scan 연동
```

## 포트폴리오 한 줄 설명

```text
NHI Secret 탐지 결과를 위험도, 정책 근거, Human Review, Audit Log까지 연결해 보안 담당자가 검토 가능한 리포트와 대시보드로 제공하는 LangGraph 기반 보안 Agent MVP를 구현했습니다.
```