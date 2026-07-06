# NHI Secret Agent

LangGraph 기반 NHI Secret 위험 분석 및 리포팅 Agent MVP.

## 목표

소스코드, 설정 파일, 문서, 로그에 노출될 수 있는 NHI Secret 후보를 탐지하고,
문맥 분석, 위험도 판단, Agent 설명, JSON/Markdown 리포트 생성을 수행한다.

## 현재 단계

4단계: 테스트 및 보안성 검증 추가

현재는 `data/sample_project` 하위 파일을 로컬에서 스캔하고,
LangGraph Workflow를 통해 Context Analysis, Risk Scoring,
Explanation, Report Node를 순차 실행한다.

추가로 pytest 기반 테스트를 작성해 다음 항목을 검증한다.

- Scanner가 샘플 Secret 후보를 탐지하는지 확인
- Secret 원문이 `result.json`, `report.md`에 저장되지 않는지 확인
- 마스킹된 Secret만 리포트에 포함되는지 확인
- LangGraph 전체 Workflow가 정상 실행되는지 확인
- Critical/High 항목이 Human Review 대상으로 분류되는지 확인

## 실행 방법

```bash
python -m app.main --target-path data/sa sample_project
```

## 주요 구조

```text
app/
├── main.py
├── agents/
│   ├── state.py
│   ├── graph.py
│   └── nodes/
│       ├── discovery_node.py
│       ├── context_node.py
│       ├── risk_node.py
│       ├── explanation_node.py
│       └── report_node.py
```

## 보안 원칙

- 실제 Secret은 사용하지 않는다.
- 리포트에는 Secret 원문을 저장하지 않는다.
- 탐지 결과는 마스킹된 값만 저장한다.
- Critical/High 등급은 자동 조치하지 않고 관리자 검토 대상으로 분류한다.
