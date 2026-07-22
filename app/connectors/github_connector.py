"""GitHub REST API와 통신하는 Connector."""

from __future__ import annotations

import os
from typing import Any

import requests

from app.connectors.base_connector import BaseConnector
from app.connectors.connector_errors import (
    AuthenticationError,
    ConnectorTimeoutError,
    ExternalApiError,
    PermissionDeniedError,
    RateLimitError,
    ResourceNotFoundError,
)
from app.connectors.schemas import (
    GitHubBranchMetadata,
    GitHubConnectionResult,
    GitHubRepositoryMetadata,
)


class GitHubConnector(BaseConnector):
    """GitHub Repository와 Branch 정보를 조회한다."""

    provider = "github"

    def __init__(
        self,
        token: str | None = None,
        api_url: str = "https://api.github.com",
        timeout_seconds: int = 10,
    ) -> None:
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.api_url = api_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "NHI-Secret-Agent",
            }
        )

        if self.token:
            self.session.headers.update(
                {
                    "Authorization": f"Bearer {self.token}",
                }
            )

    def _request(
        self,
        method: str,
        endpoint: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> requests.Response:
        """GitHub API 요청을 공통 처리한다."""
        url = f"{self.api_url}{endpoint}"

        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                timeout=self.timeout_seconds,
            )
        except requests.Timeout as exc:
            raise ConnectorTimeoutError("GitHub API 요청 시간이 초과됐습니다.") from exc
        except requests.RequestException as exc:
            raise ExternalApiError("GitHub API에 연결하지 못했습니다.") from exc

        self._raise_for_status(response)
        return response

    def _raise_for_status(self, response: requests.Response) -> None:
        """HTTP 상태 코드를 프로젝트용 예외로 변환한다."""
        if response.status_code < 400:
            return

        if response.status_code == 401:
            raise AuthenticationError("GitHub 인증에 실패했습니다. GITHUB_TOKEN을 확인하세요.")

        if response.status_code == 403:
            remaining = response.headers.get("X-RateLimit-Remaining")

            if remaining == "0":
                raise RateLimitError("GitHub API 호출 한도를 초과했습니다.")

            raise PermissionDeniedError("GitHub 자원을 조회할 권한이 없습니다.")

        if response.status_code == 404:
            raise ResourceNotFoundError("요청한 GitHub Repository 또는 Branch를 찾을 수 없습니다.")

        raise ExternalApiError(f"GitHub API 오류가 발생했습니다. HTTP 상태 코드: {response.status_code}")

    def check_connection(self) -> GitHubConnectionResult:
        """GitHub API 연결 상태와 Rate Limit을 확인한다."""
        if self.token:
            user_response = self._request("GET", "/user")
            user_data = user_response.json()
            login: str | None = user_data.get("login")
            authenticated = True
        else:
            login = None
            authenticated = False

        rate_response = self._request("GET", "/rate_limit")
        rate_data = rate_response.json()

        core_rate = rate_data.get("resources", {}).get("core", {})

        return {
            "connected": True,
            "provider": self.provider,
            "authenticated": authenticated,
            "login": login,
            "rate_limit_limit": core_rate.get("limit"),
            "rate_limit_remaining": core_rate.get("remaining"),
            "rate_limit_reset": core_rate.get("reset"),
        }

    def get_metadata(self) -> dict[str, Any]:
        """Connector 자체 설정 정보를 반환한다."""
        return {
            "provider": self.provider,
            "api_url": self.api_url,
            "authenticated": bool(self.token),
            "timeout_seconds": self.timeout_seconds,
        }

    def get_repository(
        self,
        repository: str,
    ) -> GitHubRepositoryMetadata:
        """Repository의 기본 정보를 조회한다."""
        owner, repo = self._parse_repository_name(repository)

        response = self._request(
            "GET",
            f"/repos/{owner}/{repo}",
        )
        data = response.json()

        visibility = data.get("visibility")

        if visibility is None:
            visibility = "private" if data.get("private") else "public"

        return {
            "provider": self.provider,
            "full_name": data.get("full_name", repository),
            "owner": data.get("owner", {}).get("login", owner),
            "name": data.get("name", repo),
            "html_url": data.get("html_url", ""),
            "default_branch": data.get("default_branch", ""),
            "visibility": visibility,
            "private": bool(data.get("private", False)),
            "archived": bool(data.get("archived", False)),
            "disabled": bool(data.get("disabled", False)),
            "size_kb": int(data.get("size", 0)),
            "language": data.get("language"),
            "updated_at": data.get("updated_at", ""),
            "pushed_at": data.get("pushed_at", ""),
        }

    def list_branches(
        self,
        repository: str,
        *,
        per_page: int = 100,
    ) -> list[GitHubBranchMetadata]:
        """Repository의 Branch 목록을 조회한다."""
        owner, repo = self._parse_repository_name(repository)

        response = self._request(
            "GET",
            f"/repos/{owner}/{repo}/branches",
            params={
                "per_page": per_page,
            },
        )

        branches = response.json()

        return [
            {
                "name": branch.get("name", ""),
                "commit_sha": branch.get("commit", {}).get("sha", ""),
                "protected": bool(branch.get("protected", False)),
            }
            for branch in branches
        ]

    def get_branch(
        self,
        repository: str,
        branch_name: str,
    ) -> GitHubBranchMetadata:
        """특정 Branch의 최신 Commit SHA를 조회한다."""
        owner, repo = self._parse_repository_name(repository)

        response = self._request(
            "GET",
            f"/repos/{owner}/{repo}/branches/{branch_name}",
        )
        branch = response.json()

        return {
            "name": branch.get("name", branch_name),
            "commit_sha": branch.get("commit", {}).get("sha", ""),
            "protected": bool(branch.get("protected", False)),
        }

    @staticmethod
    def _parse_repository_name(repository: str) -> tuple[str, str]:
        """owner/repository 형식을 검증한다."""
        normalized = repository.strip().strip("/")
        parts = normalized.split("/")

        if len(parts) != 2 or not all(parts):
            raise ValueError("Repository는 owner/repository 형식으로 입력해야 합니다. 예: KoYejun/NHI_Project")

        return parts[0], parts[1]
