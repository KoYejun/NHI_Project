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
