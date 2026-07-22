"""Slack Connector 단위 테스트."""

from unittest.mock import Mock

from app.connectors.slack_connector import SlackConnector


def test_connector_metadata_without_token() -> None:
    connector = SlackConnector()

    metadata = connector.get_metadata()

    assert metadata["provider"] == "slack"
    assert metadata["api_url"] == "https://slack.com/api"
    assert metadata["authenticated"] is False
    assert metadata["timeout_seconds"] == 10


def test_check_connection_without_token() -> None:
    connector = SlackConnector()

    result = connector.check_connection()

    assert result["connected"] is False
    assert result["authenticated"] is False
    assert result["validation_status"] == "UNVERIFIED"
    assert result["error_code"] == "TOKEN_NOT_PROVIDED"


def test_validate_active_bot_token(
    monkeypatch,
) -> None:
    connector = SlackConnector()

    response = Mock()
    response.json.return_value = {
        "ok": True,
        "url": "https://example.slack.com/",
        "team": "Example Workspace",
        "user": "security-bot",
        "team_id": "T01234567",
        "user_id": "U01234567",
        "bot_id": "B01234567",
        "app_id": "A01234567",
    }
    response.headers = {"X-OAuth-Scopes": "chat:write,channels:history"}

    monkeypatch.setattr(
        connector,
        "_request",
        Mock(return_value=response),
    )

    result = connector.validate_token("xoxb-FAKE-TEST-TOKEN")

    assert result["authenticated"] is True
    assert result["validation_status"] == "VERIFIED_ACTIVE"
    assert result["identity_type"] == "BOT"
    assert result["bot_id"] == "B01234567"
    assert result["team_id"] == "T01234567"
    assert result["raw_scopes"] == [
        "chat:write",
        "channels:history",
    ]


def test_validate_revoked_token(
    monkeypatch,
) -> None:
    connector = SlackConnector()

    response = Mock()
    response.json.return_value = {
        "ok": False,
        "error": "token_revoked",
    }
    response.headers = {}

    monkeypatch.setattr(
        connector,
        "_request",
        Mock(return_value=response),
    )

    result = connector.validate_token("xoxb-FAKE-REVOKED-TOKEN")

    assert result["authenticated"] is False
    assert result["validation_status"] == "VERIFIED_INACTIVE"
    assert result["error_code"] == "TOKEN_REVOKED"


def test_validate_invalid_token(
    monkeypatch,
) -> None:
    connector = SlackConnector()

    response = Mock()
    response.json.return_value = {
        "ok": False,
        "error": "invalid_auth",
    }
    response.headers = {}

    monkeypatch.setattr(
        connector,
        "_request",
        Mock(return_value=response),
    )

    result = connector.validate_token("xoxb-FAKE-INVALID-TOKEN")

    assert result["validation_status"] == "VERIFIED_INACTIVE"
    assert result["error_code"] == "INVALID_AUTH"


def test_extract_scopes_from_header() -> None:
    response = Mock()
    response.headers = {"X-OAuth-Scopes": "chat:write, channels:history, files:read"}

    result = SlackConnector._extract_scopes(response)

    assert result == [
        "chat:write",
        "channels:history",
        "files:read",
    ]
