"""Provider별 Credential Validator를 선택한다."""

from __future__ import annotations

from typing import Any

from app.validation.base_validator import BaseValidator
from app.validation.slack_validator import SlackValidator


class ValidationService:
    """Finding의 Provider에 맞는 검증기를 실행한다."""

    def __init__(
        self,
        validators: dict[str, BaseValidator] | None = None,
    ) -> None:
        self.validators = validators or {
            "slack": SlackValidator(),
        }

    def validate_credential(
        self,
        *,
        provider: str,
        credential: str,
    ) -> dict[str, Any]:
        """Provider와 Credential을 받아 검증 결과를 반환한다."""
        normalized_provider = provider.strip().lower()

        validator = self.validators.get(normalized_provider)

        if validator is None:
            return {
                "status": "NOT_SUPPORTED",
                "provider": normalized_provider or "unknown",
                "raw_scopes": [],
                "error_code": "VALIDATOR_NOT_SUPPORTED",
                "error_message": ("현재 Provider의 Token 검증 기능을 지원하지 않습니다."),
            }

        if not credential:
            return {
                "status": "VALIDATION_FAILED",
                "provider": normalized_provider,
                "raw_scopes": [],
                "error_code": "CREDENTIAL_NOT_PROVIDED",
                "error_message": "검증할 Credential이 없습니다.",
            }

        return validator.validate(credential)
