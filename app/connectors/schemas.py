"""Connector가 반환하는 데이터의 타입 정의."""

from typing import TypedDict


class GitHubConnectionResult(TypedDict, total=False):
    connected: bool
    provider: str
    authenticated: bool
    login: str | None
    rate_limit_limit: int | None
    rate_limit_remaining: int | None
    rate_limit_reset: int | None


class GitHubRepositoryMetadata(TypedDict, total=False):
    provider: str
    full_name: str
    owner: str
    name: str
    html_url: str
    default_branch: str
    visibility: str
    private: bool
    archived: bool
    disabled: bool
    size_kb: int
    language: str | None
    updated_at: str
    pushed_at: str


class GitHubBranchMetadata(TypedDict, total=False):
    name: str
    commit_sha: str
    protected: bool


class GitHubCloneResult(TypedDict, total=False):
    provider: str
    repository: str
    branch: str
    commit_sha: str
    clone_path: str
    clone_url: str

class SlackConnectionResult(TypedDict, total=False):
    connected: bool
    provider: str
    authenticated: bool
    validation_status: str
    identity_type: str
    identity_id: str
    identity_name: str
    user_id: str
    bot_id: str
    team_id: str
    team_name: str
    enterprise_id: str
    app_id: str
    raw_scopes: list[str]
    checked_at: str
    error_code: str
    error_message: str