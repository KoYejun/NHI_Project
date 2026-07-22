"""외부 서비스 Connector에서 사용하는 공통 예외 클래스."""


class ConnectorError(Exception):
    """Connector 실행 과정에서 발생하는 기본 예외."""

    error_code = "CONNECTOR_ERROR"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class AuthenticationError(ConnectorError):
    """인증 정보가 없거나 유효하지 않은 경우."""

    error_code = "AUTHENTICATION_FAILED"


class PermissionDeniedError(ConnectorError):
    """인증은 됐지만 대상 자원에 대한 권한이 없는 경우."""

    error_code = "PERMISSION_DENIED"


class ResourceNotFoundError(ConnectorError):
    """Repository나 Branch를 찾을 수 없는 경우."""

    error_code = "RESOURCE_NOT_FOUND"


class RateLimitError(ConnectorError):
    """GitHub API 호출 한도를 초과한 경우."""

    error_code = "RATE_LIMIT_EXCEEDED"


class ExternalApiError(ConnectorError):
    """외부 API에서 예상하지 못한 오류가 발생한 경우."""

    error_code = "EXTERNAL_API_ERROR"


class ConnectorTimeoutError(ConnectorError):
    """외부 API 요청 시간이 제한 시간을 초과한 경우."""

    error_code = "CONNECTOR_TIMEOUT"


class RepositoryCloneError(ConnectorError):
    """Git Repository를 내려받지 못한 경우."""

    error_code = "REPOSITORY_CLONE_FAILED"


class GitCommandNotFoundError(ConnectorError):
    """실행 환경에서 Git 명령어를 찾을 수 없는 경우."""

    error_code = "GIT_COMMAND_NOT_FOUND"
