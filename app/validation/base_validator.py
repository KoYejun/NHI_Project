"""Credential Validator의 공통 인터페이스."""

from abc import ABC, abstractmethod
from typing import Any


class BaseValidator(ABC):
    """Provider별 Credential 검증기가 구현할 기본 클래스."""

    provider: str

    @abstractmethod
    def validate(
        self,
        credential: str,
    ) -> dict[str, Any]:
        """Credential을 검증하고 정규화된 결과를 반환한다."""
