# NHI Secret Agent

LangGraph 기반 NHI Secret 위험 분석 및 리포팅 Agent MVP.

## 목표

소스코드, 설정 파일, 문서, 로그에 노출될 수 있는 NHI Secret 후보를 탐지하고,
문맥 분석, 위험도 판단, Agent 설명, JSON/Markdown 리포트 생성을 수행한다.

## 현재 단계

1단계: LangGraph Workflow 실행 뼈대 구현

현재는 실제 Secret Scanner 연동 전이며,
Discovery → Context → Risk → Explanation → Report Node가 순서대로 실행되는 구조를 먼저 구현한다.

## 실행 방법

```bash
python -m app.main --target-path data/sample_project
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