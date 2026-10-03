from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol


class NewsFailureKind(str, Enum):
    TIMEOUT = "TIMEOUT"
    HTTP = "HTTP"
    NETWORK = "NETWORK"
    INVALID_PAYLOAD = "INVALID_PAYLOAD"
    EMPTY = "EMPTY"


@dataclass(frozen=True)
class NewsQuery:
    symbol: str | None = None
    category: str = "MARKET"
    limit: int = 20


class NewsProviderError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        provider: str,
        kind: NewsFailureKind,
    ) -> None:
        super().__init__(message)
        self.provider = provider
        self.kind = kind


class NewsProvider(Protocol):
    name: str

    def fetch(self, query: NewsQuery) -> list:
        ...
