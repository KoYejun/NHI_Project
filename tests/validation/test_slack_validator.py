"""Slack Validator 단위 테스트."""

from unittest.mock import Mock

from app.validation.slack_validator import SlackValidator


def test_slack_validator_returns_normalized_result() -> None:
    connector = Mock()
    connector.validate_token.return_value = {
        "validation_status": "VERIFIED_ACTIVE",
        "provider": "slack",
        "checked_at": "2026-07-22T12:00:00",
        "identity_type": "BOT",
        "identity_id": "B01234567",
        "identity_name": "security-bot",
        "bot_id": "B01234567",
        "team_id": "T01234567",
        "team_name": "Example Workspace",
        "raw_scopes": [
            "chat:write",
        ],
    }

    validator = SlackValidator(connector=connector)

    result = validator.validate("xoxb-FAKE-TEST-TOKEN")

    assert result["status"] == "VERIFIED_ACTIVE"
    assert result["provider"] == "slack"
    assert result["identity_type"] == "BOT"
    assert result["identity_id"] == "B01234567"
    assert result["raw_scopes"] == ["chat:write"]


def test_slack_validator_does_not_return_token() -> None:
    connector = Mock()
    connector.validate_token.return_value = {
        "validation_status": "VERIFIED_ACTIVE",
        "provider": "slack",
        "raw_scopes": [],
    }

    validator = SlackValidator(connector=connector)

    result = validator.validate("xoxb-FAKE-TEST-TOKEN")

    assert "token" not in result
    assert "credential" not in result
    assert "secret_value" not in result
