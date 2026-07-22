"""Slack Web API와 통신하는 Connector."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import requests

from app.connectors.base_connector import BaseConnector
from app.connectors.connector_errors import (
    ConnectorTimeoutError,
    ExternalApiError,
)
from app.connectors.schemas import SlackConnectionResult


class SlackConnector(BaseConnector):
    """Slack Token의 유효성과 연결된 Identity를 조회한다."""

    provider = "slack"

    def __init__(
        self,
        token: str | None = None,
        api_url: str = "https://slack.com/api",
        timeout_seconds: int = 10,
    ) -> None:
        self.token = token
        self.api_url = api_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/json",
                "User-Agent": "NHI-Secret-Agent",
            }
        )

    def _request(
        self,
        method_name: str,
        *,
        token: str | None = None,
        params: dict[str, Any] | None = None,
    ) -> requests.Response:
        """Slack Web API 메서드를 호출한다."""
        credential = token or self.token

        if not credential:
            raise ValueError("Slack Token이 제공되지 않았습니다.")

        url = f"{self.api_url}/{method_name}"

        headers = {
            "Authorization": f"Bearer {credential}",
        }

        try:
            response = self.session.post(
                url,
                headers=headers,
                data=params or {},
                timeout=self.timeout_seconds,
            )
        except requests.Timeout as exc:
            raise ConnectorTimeoutError("Slack API 요청 시간이 초과됐습니다.") from exc
        except requests.RequestException as exc:
            raise ExternalApiError("Slack API에 연결하지 못했습니다.") from exc

        if response.status_code >= 500:
            raise ExternalApiError(f"Slack API 서버 오류가 발생했습니다. HTTP 상태 코드: {response.status_code}")

        if response.status_code == 429:
            raise ExternalApiError("Slack API 호출 한도를 초과했습니다.")

        return response

    def check_connection(self) -> SlackConnectionResult:
        """생성자에 등록된 Token의 인증 상태를 검사한다."""
        if not self.token:
            return {
                "connected": False,
                "provider": self.provider,
                "authenticated": False,
                "validation_status": "UNVERIFIED",
                "error_code": "TOKEN_NOT_PROVIDED",
                "error_message": "Slack Token이 제공되지 않았습니다.",
            }

        return self.validate_token(self.token)

    def get_metadata(self) -> dict[str, Any]:
        """Slack Connector 설정 정보를 반환한다."""
        return {
            "provider": self.provider,
            "api_url": self.api_url,
            "authenticated": bool(self.token),
            "timeout_seconds": self.timeout_seconds,
        }

    def validate_token(
        self,
        token: str,
    ) -> SlackConnectionResult:
        """
        Slack auth.test를 이용해 Token의 유효성을 검사한다.

        Token 원문은 반환 데이터에 포함하지 않는다.
        """
        checked_at = datetime.now().isoformat(timespec="seconds")

        response = self._request(
            "auth.test",
            token=token,
        )

        try:
            data = response.json()
        except ValueError as exc:
            raise ExternalApiError("Slack API 응답을 JSON으로 해석하지 못했습니다.") from exc

        raw_scopes = self._extract_scopes(response)

        if not data.get("ok", False):
            error_code = str(data.get("error", "unknown_error"))

            return {
                "connected": True,
                "provider": self.provider,
                "authenticated": False,
                "validation_status": self._map_error_status(error_code),
                "raw_scopes": raw_scopes,
                "checked_at": checked_at,
                "error_code": error_code.upper(),
                "error_message": self._build_safe_error_message(error_code),
            }

        bot_id = str(data.get("bot_id") or "")
        user_id = str(data.get("user_id") or "")
        identity_type = "BOT" if bot_id else "USER"

        identity_id = bot_id or user_id
        identity_name = str(data.get("user") or data.get("bot") or identity_id)

        return {
            "connected": True,
            "provider": self.provider,
            "authenticated": True,
            "validation_status": "VERIFIED_ACTIVE",
            "identity_type": identity_type,
            "identity_id": identity_id,
            "identity_name": identity_name,
            "user_id": user_id,
            "bot_id": bot_id,
            "team_id": str(data.get("team_id") or ""),
            "team_name": str(data.get("team") or ""),
            "enterprise_id": str(data.get("enterprise_id") or ""),
            "app_id": str(data.get("app_id") or ""),
            "raw_scopes": raw_scopes,
            "checked_at": checked_at,
        }

    @staticmethod
    def _extract_scopes(
        response: requests.Response,
    ) -> list[str]:
        """Slack 응답 헤더에서 OAuth Scope 목록을 추출한다."""
        scope_header = response.headers.get("X-OAuth-Scopes") or response.headers.get("x-oauth-scopes") or ""

        return [scope.strip() for scope in scope_header.split(",") if scope.strip()]

    @staticmethod
    def _map_error_status(error_code: str) -> str:
        """Slack 오류 코드를 검증 상태로 변환한다."""
        inactive_errors = {
            "invalid_auth",
            "token_revoked",
            "account_inactive",
            "not_authed",
        }

        if error_code in inactive_errors:
            return "VERIFIED_INACTIVE"

        return "VALIDATION_FAILED"

    @staticmethod
    def _build_safe_error_message(
        error_code: str,
    ) -> str:
        """Token 원문을 포함하지 않는 사용자용 메시지를 반환한다."""
        messages = {
            "invalid_auth": "Slack Token 인증에 실패했습니다.",
            "token_revoked": "Slack Token이 폐기됐습니다.",
            "account_inactive": ("Slack 계정 또는 App이 비활성 상태입니다."),
            "not_authed": "Slack 인증 정보가 없습니다.",
            "missing_scope": ("Slack API 조회에 필요한 Scope가 부족합니다."),
        }

        return messages.get(
            error_code,
            "Slack Token 검증 중 오류가 발생했습니다.",
        )
