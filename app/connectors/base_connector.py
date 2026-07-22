"""외부 서비스 Connector의 공통 인터페이스."""

from abc import ABC, abstractmethod
from typing import Any


class BaseConnector(ABC):
    """모든 외부 서비스 Connector가 구현해야 하는 기본 클래스."""

    provider: str

    @abstractmethod
    def check_connection(self) -> dict[str, Any]:
        """외부 서비스와 정상적으로 통신 가능한지 확인한다."""

    @abstractmethod
    def get_metadata(self) -> dict[str, Any]:
        """연결된 외부 서비스의 기본 메타데이터를 반환한다."""
