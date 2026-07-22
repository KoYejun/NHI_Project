"""Slack Token 검증기."""

from __future__ import annotations

from typing import Any

from app.connectors.connector_errors import ConnectorError
from app.connectors.slack_connector import SlackConnector
from app.validation.base_validator import BaseValidator


class SlackValidator(BaseValidator):
    """Slack Token을 Slack API로 검증한다."""

    provider = "slack"

    def __init__(
        self,
        connector: SlackConnector | None = None,
    ) -> None:
        self.connector = connector or SlackConnector()

    def validate(
        self,
        credential: str,
    ) -> dict[str, Any]:
        """Slack Token 검증 결과를 Finding용 형식으로 반환한다."""
        try:
            result = self.connector.validate_token(credential)
        except ConnectorError as exc:
            return {
                "status": "VALIDATION_FAILED",
                "provider": self.provider,
                "raw_scopes": [],
                "error_code": exc.error_code,
                "error_message": exc.message,
            }
        except ValueError as exc:
            return {
                "status": "VALIDATION_FAILED",
                "provider": self.provider,
                "raw_scopes": [],
                "error_code": "INVALID_INPUT",
                "error_message": str(exc),
            }

        return {
            "status": result.get(
                "validation_status",
                "VALIDATION_FAILED",
            ),
            "provider": self.provider,
            "checked_at": result.get("checked_at", ""),
            "identity_type": result.get("identity_type", ""),
            "identity_id": result.get("identity_id", ""),
            "identity_name": result.get("identity_name", ""),
            "user_id": result.get("user_id", ""),
            "bot_id": result.get("bot_id", ""),
            "team_id": result.get("team_id", ""),
            "team_name": result.get("team_name", ""),
            "enterprise_id": result.get("enterprise_id", ""),
            "app_id": result.get("app_id", ""),
            "raw_scopes": result.get("raw_scopes", []),
            "error_code": result.get("error_code", ""),
            "error_message": result.get("error_message", ""),
        }
