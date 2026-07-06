# 데모 체크리스트

## 1. 환경 준비

```bash
.\.venv\Scripts\activate
```

## 2. 샘플 프로젝트 생성

```bash
python scripts/create_sample_project.py
```

확인:

```bash
dir data\sample_project
```

## 3. Agent 실행

```bash
python -m app.main --target-path data/sample_project
```

예상 결과:

```text
Raw Findings: 4
Context Results: 4
Risk Results: 4
Explanations: 4
Report Path: reports/report.md
Errors: 0
```

## 4. 리포트 확인

```bash
Get-Content -Encoding UTF8 reports\report.md
```

## 5. JSON 결과 확인

```bash
Get-Content -Encoding UTF8 reports\result.json
```

## 6. Secret 원문 미포함 확인

```bash
Select-String -Path reports\report.md,reports\result.json -Pattern "AKIA1234567890ABCDEF"
```

출력이 없어야 한다.

## 7. 테스트 실행

```bash
python -m pytest -q
```

## 8. 코드 품질 검사

```bash
python -m ruff format app tests scripts
python -m ruff check app tests scripts
```

## 9. 발표에서 보여줄 화면

- 프로젝트 폴더 구조
- LangGraph Workflow 코드
- sample_project 생성 스크립트
- 실행 결과 터미널
- result.json
- report.md
- pytest 통과 화면
- Secret 원문 미포함 확인 화면