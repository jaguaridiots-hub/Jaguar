from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class NewsItem:
    item_id: str
    publisher: str
    title: str
    published_at: str
    url: str
    symbol: str | None
    category: str
    source: str
    cached: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.item_id,
            "publisher": self.publisher,
            "title": self.title,
            "published_at": self.published_at,
            "url": self.url,
            "symbol": self.symbol,
            "category": self.category,
            "source": self.source,
            "cached": self.cached,
        }


@dataclass(frozen=True)
class NewsSnapshot:
    status: str
    provider: str
    symbol: str | None
    category: str
    items: tuple[NewsItem, ...]
    cached: bool
    fetched_at: str | None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "provider": self.provider,
            "symbol": self.symbol,
            "category": self.category,
            "items": [item.to_dict() for item in self.items],
            "cached": self.cached,
            "fetched_at": self.fetched_at,
            "error": self.error,
        }
