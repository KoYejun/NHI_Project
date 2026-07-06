# NHI Access Policy

## 목적

CI/CD, 서비스 계정, 자동화 봇, 클라우드 애플리케이션 등 Non-Human Identity의 접근권한을 안전하게 관리한다.

## 주요 기준

- NHI는 최소권한 원칙에 따라 필요한 권한만 가져야 한다.
- 고위험 Secret이 발견되면 연결된 서비스 계정, 자동화 계정, 토큰 범위, 최근 접근 로그를 점검한다.
- 소유자가 불명확한 NHI는 담당자 확인 및 재승인 대상으로 분류한다.
- 장기간 사용되지 않은 NHI Token은 회수 또는 재승인을 검토한다.
- Critical 또는 High 위험 항목은 자동 조치하지 않고 관리자 검토 대상으로 분류한다.

## 적용 대상

- CI/CD Token
- GitHub Actions Token
- AWS IAM Access Key
- OAuth Client Secret
- Service Account Credential
- Bot Token

## 대응 권고

- NHI 소유자 확인
- 권한 범위 점검
- 최근 접근 로그 확인
- 불필요 권한 축소
- 관리자 재승인 요청