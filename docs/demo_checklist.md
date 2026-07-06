# Demo Checklist

이 문서는 NHI Secret Agent 프로젝트를 시연할 때 따라야 하는 실행 순서와 확인 항목을 정리한다.

현재 데모 범위는 다음과 같다.

```text
샘플 프로젝트 생성
→ Secret 탐지
→ 문맥 분석
→ 위험도 산정
→ 정책 근거 검색
→ Agent 설명 생성
→ Human Review 상태 분류
→ JSON / Markdown 리포트 생성
→ Streamlit 대시보드 확인
→ Review 결정 저장
→ Audit Log 확인
→ 테스트 / Ruff / Quality Gate 검증
```

---

## 1. 프로젝트 루트 확인

PowerShell에서 프로젝트 루트에 있는지 확인한다.

```powershell
pwd
```

정상 위치 예시:

```text
C:\Users\kyjha\OneDrive\바탕 화면\nhi-secret-agent
```

---

## 2. 가상환경 활성화

```powershell
.\.venv\Scripts\activate
```

정상적으로 활성화되면 프롬프트 앞에 `(.venv)`가 표시된다.

```text
(.venv) PS C:\Users\...\nhi-secret-agent>
```

---

## 3. 의존성 설치 확인

처음 실행하거나 패키지가 누락된 경우 아래 명령어를 실행한다.

```powershell
pip install -r requirements.txt
```

주요 패키지 확인:

```powershell
pip show langgraph
pip show typer
pip show pytest
pip show ruff
pip show streamlit
pip show pandas
```

---

## 4. 샘플 프로젝트 생성

보안상 `data/sample_project` 내부의 샘플 파일은 Git에 직접 저장하지 않는다.  
아래 스크립트로 로컬에 데모용 샘플 프로젝트를 생성한다.

```powershell
python scripts\create_sample_project.py
```

생성 확인:

```powershell
dir data\sample_project
```

예상 파일:

```text
.env
app.py
config.yml
server.log
README.md
.gitkeep
```

주의:

```text
이 파일들은 테스트용 가짜 Secret을 포함하지만,
Git에는 직접 올라가지 않도록 .gitignore로 제외한다.
```

---

## 5. Agent 실행

```powershell
python -m app.main --target-path data/sample_project
```

예상 출력:

```text
[Discovery Node] 실행
[Context Analysis Node] 실행
[Risk Scoring Node] 실행
[Policy Evidence Node] 실행
[Explanation Node] 실행
[Human Review Node] 실행
[Report Node] 실행

=== NHI Secret Agent 실행 완료 ===
Target Path: data/sample_project
Raw Findings: 4
Context Results: 4
Risk Results: 4
Policy Evidence: 4
Explanations: 4
Review Results: 4
Report Path: reports/report.md
Errors: 0
```

확인할 점:

```text
Raw Findings: 4
Policy Evidence: 4
Review Results: 4
Errors: 0
```

---

## 6. 생성된 리포트 확인

Markdown 리포트 확인:

```powershell
Get-Content -Encoding UTF8 reports\report.md
```

JSON 결과 확인:

```powershell
Get-Content -Encoding UTF8 reports\result.json
```

생성되어야 하는 파일:

```text
reports/result.json
reports/report.md
```

리포트에서 확인할 섹션:

```text
1. 요약
2. 상세 탐지 결과
3. 점수 산정 근거
4. 문맥 분석
5. 정책 근거
6. Agent 분석
7. Human Review 상태
8. 보안 설계 원칙
```

---

## 7. Secret 원문 미포함 확인

PowerShell에서 아래 명령어를 실행한다.

```powershell
$awsPattern = "AKIA" + "1234567890ABCDEF"
$githubPattern = "ghp_" + "abcdefghijklmnopqrstuvwxyz1234567890"
$clientSecretPattern = "sample_client_secret_" + "abcdefghijklmnopqrstuvwxyz"
$bearerPattern = "sampleBearerToken" + "1234567890abcdef"

Select-String -Path reports\report.md,reports\result.json -Pattern $awsPattern
Select-String -Path reports\report.md,reports\result.json -Pattern $githubPattern
Select-String -Path reports\report.md,reports\result.json -Pattern $clientSecretPattern
Select-String -Path reports\report.md,reports\result.json -Pattern $bearerPattern
```

정상 결과:

```text
아무것도 출력되지 않아야 한다.
```

확인 의미:

```text
리포트와 JSON 결과에 Secret 원문이 저장되지 않고,
마스킹된 값만 포함되어야 한다.
```

---

## 8. Streamlit 대시보드 실행

```powershell
streamlit run frontend/streamlit_app.py
```

브라우저 주소 예시:

```text
http://localhost:8501
```

대시보드에서 확인할 화면:

```text
1. Summary KPI 카드
2. Risk & Review Distribution 차트
3. Finding Overview 탭
4. Finding Detail 탭
5. Review Workflow 탭
6. Policy Evidence 탭
7. Audit Log 탭
8. Raw JSON 탭
```

---

## 9. Summary KPI 확인

대시보드 상단에서 다음 값이 표시되는지 확인한다.

```text
Total
Critical
High
Human Review
Pending Review
Reviewed
```

예상 상태:

```text
Total: 4
Critical: 1
High: 1
Human Review: 2
Pending Review: 2
Reviewed: 0
```

단, Review Workflow에서 검토 결정을 저장한 뒤에는 `Reviewed` 값이 증가할 수 있다.

---

## 10. Finding Overview 확인

`Finding Overview` 탭에서 확인할 컬럼:

```text
finding_id
secret_type
file_path
line_number
risk_score
risk_level
requires_human_review
review_status
reviewer
reviewed_at
file_type
environment_hint
file_criticality
```

확인할 필터:

```text
위험 등급 필터
Review 상태 필터
```

---

## 11. Finding Detail 확인

`Finding Detail` 탭에서 각 Finding을 선택해 아래 내용이 표시되는지 확인한다.

```text
기본 정보
Review 상태
점수 산정 근거
문맥 분석
Agent 분석
```

특히 확인할 항목:

```text
Secret 원문이 아니라 masked_secret만 표시되는지
risk_score와 risk_level이 표시되는지
policy_basis가 표시되는지
human_review 설명이 표시되는지
```

---

## 12. Policy Evidence 확인

`Policy Evidence` 탭에서 각 Finding별로 관련 정책 근거가 표시되는지 확인한다.

확인할 항목:

```text
Policy ID
Policy Title
Relevance Score
Summary
```

정책 문서 위치:

```text
data/policies/secret_management_policy.md
data/policies/nhi_access_policy.md
data/policies/incident_response_policy.md
```

---

## 13. Human Review Workflow 확인

`Review Workflow` 탭에서 Critical 또는 High 항목이 Review Queue에 표시되는지 확인한다.

예상 Review 대상:

```text
Critical 항목
High 항목
```

예상 제외 대상:

```text
Medium 항목
Low 항목
```

테스트 입력 예시:

```text
Finding: finding_001
Review 결정: APPROVED_ROTATION
Reviewer: security_admin
Review Note: 테스트용 승인 기록
```

저장 버튼:

```text
Save Review Decision
```

저장 후 기대 결과:

```text
Review 상태가 변경된다.
reports/review_status.json 파일이 생성된다.
reports/audit_log.jsonl 파일이 생성된다.
Audit Log 탭에 변경 이력이 표시된다.
```

---

## 14. Review 상태 파일 확인

Review 결정을 저장한 뒤 PowerShell에서 확인한다.

```powershell
Get-Content -Encoding UTF8 reports\review_status.json
```

확인할 필드:

```text
finding_id
status
reviewer
note
reviewed_at
```

예상 상태 예시:

```text
APPROVED_ROTATION
FALSE_POSITIVE
ACCEPTED_RISK
RESOLVED
WAITING_HUMAN_REVIEW
```

---

## 15. Audit Log 확인

Review 결정을 저장한 뒤 PowerShell에서 확인한다.

```powershell
Get-Content -Encoding UTF8 reports\audit_log.jsonl
```

확인할 필드:

```text
event_time
event_type
finding_id
status
reviewer
note
```

확인 의미:

```text
관리자 검토 결정이 감사 가능한 JSONL 로그로 기록된다.
```

주의:

```text
본 기능은 실제 Secret 폐기나 권한 회수를 수행하지 않는다.
관리자 검토 상태와 감사 증적만 관리한다.
```

---

## 16. 테스트 실행

```powershell
python -m pytest -q
```

정상 결과:

```text
모든 테스트가 통과해야 한다.
```

주요 테스트 범위:

```text
Secret 마스킹 검증
Secret Scanner 검증
LangGraph 전체 실행 검증
Policy Evidence 검증
Human Review / Audit Log 검증
Secret 원문 미저장 검증
```

---

## 17. Ruff 실행

자동 수정:

```powershell
python -m ruff check app tests scripts frontend --fix
python -m ruff format app tests scripts frontend
```

검사:

```powershell
python -m ruff check app tests scripts frontend
python -m ruff format --check app tests scripts frontend
```

정상 결과:

```text
All checks passed!
```

또는 format check에서:

```text
All checks passed!
```

---

## 18. Quality Gate 실행

공개 저장소에 올리기 전 전체 품질 검사를 실행한다.

```powershell
python scripts\quality_gate.py
```

정상 결과:

```text
[PASS] Required files exist.
[PASS] data/sample_project only tracks .gitkeep.
[PASS] reports output files are not tracked.
[PASS] No raw-looking secret patterns found in tracked files.
[PASS] Generated reports do not contain raw-looking secrets.
[PASS] Quality gate completed successfully.
```

주의:

```text
quality_gate.py는 현재 실행 중인 Python 환경을 사용해야 한다.
따라서 .venv가 활성화된 상태에서 실행한다.
```

가상환경 Python 직접 실행:

```powershell
.\.venv\Scripts\python.exe scripts\quality_gate.py
```

---

## 19. Git 추적 상태 확인

샘플 프로젝트 추적 상태 확인:

```powershell
git ls-files data/sample_project
```

정상 결과:

```text
data/sample_project/.gitkeep
```

reports 추적 상태 확인:

```powershell
git ls-files reports
```

정상 결과:

```text
reports/.gitkeep
```

Git 상태 확인:

```powershell
git status
```

아래 파일들은 Git에 올라가면 안 된다.

```text
reports/result.json
reports/report.md
reports/review_status.json
reports/audit_log.jsonl
data/sample_project/.env
data/sample_project/app.py
data/sample_project/config.yml
data/sample_project/server.log
```

만약 추적 대상에 잡히면 아래 명령어로 제거한다.

```powershell
git rm --cached reports/result.json reports/report.md reports/review_status.json reports/audit_log.jsonl
git rm --cached -r data/sample_project
git add data/sample_project/.gitkeep reports/.gitkeep
```

파일이 없다는 오류가 나오면 무시해도 된다.

---

## 20. Git 추적 파일 내 raw-looking Secret 확인

PowerShell에서 아래 명령어를 실행한다.

```powershell
$awsPattern = "AKIA" + "1234567890ABCDEF"
$githubPattern = "ghp_" + "abcdefghijklmnopqrstuvwxyz1234567890"
$clientSecretPattern = "sample_client_secret_" + "abcdefghijklmnopqrstuvwxyz"
$bearerPattern = "sampleBearerToken" + "1234567890abcdef"

git grep -n $awsPattern
git grep -n $githubPattern
git grep -n $clientSecretPattern
git grep -n $bearerPattern
```

정상 결과:

```text
아무것도 출력되지 않아야 한다.
```

주의:

```text
문서나 테스트 코드에도 raw-looking Secret 문자열을 한 덩어리로 쓰지 않는다.
필요하면 문자열을 나누어 작성한다.
```

---

## 21. GitHub Actions CI 확인

CI 파일 위치:

```text
.github/workflows/ci.yml
```

CI에서 수행하는 작업:

```text
1. Python 3.11 환경 구성
2. 의존성 설치
3. 샘플 프로젝트 생성
4. Agent 실행
5. pytest 실행
6. Ruff format check
7. Ruff lint check
8. Quality Gate 실행
```

GitHub에 push한 뒤 Actions 탭에서 CI가 통과하는지 확인한다.

---

## 22. 데모 발표 순서

시연할 때는 아래 순서가 가장 자연스럽다.

```text
1. 프로젝트 목적 설명
2. 폴더 구조 설명
3. LangGraph Workflow 설명
4. sample_project 생성
5. Agent 실행
6. result.json 확인
7. report.md 확인
8. Streamlit 대시보드 실행
9. Critical / High 항목 확인
10. Policy Evidence 확인
11. Review Workflow에서 검토 결정 저장
12. Audit Log 확인
13. pytest / quality_gate 통과 화면 제시
```

---

## 23. 데모에서 강조할 포인트

```text
1. Secret 원문을 저장하지 않고 마스킹된 값만 남긴다.
2. 단순 탐지가 아니라 위험도 점수와 등급을 산정한다.
3. 정책 문서 기반 근거를 연결한다.
4. Critical / High 항목은 자동 조치하지 않고 Human Review 대상으로 분류한다.
5. Review 결정은 Audit Log로 남긴다.
6. 실제 Secret 폐기, 권한 회수, 외부 API 호출은 수행하지 않는다.
7. 테스트와 Quality Gate로 보안 설계 원칙을 검증한다.
```

---

## 24. 데모 완료 기준

아래가 모두 확인되면 데모 준비 완료다.

```text
1. python scripts/create_sample_project.py 성공
2. python -m app.main --target-path data/sample_project 성공
3. reports/result.json 생성
4. reports/report.md 생성
5. Streamlit 대시보드 실행 성공
6. Review Workflow에서 검토 결정 저장 성공
7. reports/review_status.json 생성
8. reports/audit_log.jsonl 생성
9. python -m pytest -q 성공
10. python -m ruff check app tests scripts frontend 성공
11. python scripts/quality_gate.py 성공
12. data/sample_project에는 .gitkeep만 Git 추적
13. reports에는 .gitkeep만 Git 추적
14. raw-looking Secret 문자열이 Git 추적 파일에 없음
```