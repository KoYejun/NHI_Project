# Secret Management Policy

## 목적

Secret, API Key, Access Token, Client Secret, Private Key 등 인증정보가 소스코드, 설정 파일, 문서, 로그에 저장되는 것을 방지한다.

## 주요 기준

- 운영 환경 Secret은 소스코드와 설정 파일에 평문으로 저장하지 않는다.
- Secret은 전용 Secret Manager 또는 안전한 환경변수 관리 체계를 통해 관리한다.
- Secret 노출이 의심되는 경우 즉시 폐기 및 재발급을 검토한다.
- 리포트와 로그에는 Secret 원문을 저장하지 않고 마스킹된 값만 기록한다.
- 저장소 히스토리, 배포 로그, 오류 로그에 Secret이 남아 있는지 확인한다.

## 적용 대상

- AWS Access Key
- GitHub Token
- Bearer Token
- Client Secret
- API Key
- Private Key

## 대응 권고

- Secret 재발급
- Secret Manager 이전
- pre-commit Secret Scan 적용
- 저장소 히스토리 점검
- 로그 마스킹 정책 적용