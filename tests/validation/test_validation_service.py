"""Validation Service 단위 테스트."""

from unittest.mock import Mock

from app.validation.validation_service import ValidationService


def test_unsupported_provider() -> None:
    service = ValidationService(validators={})

    result = service.validate_credential(
        provider="github",
        credential="fake-credential",
    )

    assert result["status"] == "NOT_SUPPORTED"
    assert result["provider"] == "github"


def test_missing_credential() -> None:
    validator = Mock()

    service = ValidationService(
        validators={
            "slack": validator,
        }
    )

    result = service.validate_credential(
        provider="slack",
        credential="",
    )

    assert result["status"] == "VALIDATION_FAILED"
    assert result["error_code"] == "CREDENTIAL_NOT_PROVIDED"
    validator.validate.assert_not_called()


def test_supported_provider_calls_validator() -> None:
    validator = Mock()
    validator.validate.return_value = {
        "status": "VERIFIED_ACTIVE",
        "provider": "slack",
        "raw_scopes": [
            "chat:write",
        ],
    }

    service = ValidationService(
        validators={
            "slack": validator,
        }
    )

    result = service.validate_credential(
        provider="SLACK",
        credential="xoxb-FAKE-TEST-TOKEN",
    )

    assert result["status"] == "VERIFIED_ACTIVE"
    validator.validate.assert_called_once()
