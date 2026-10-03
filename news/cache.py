from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class _CacheEntry:
    value: object
    stored_at: float


class NewsCache:
    def __init__(
        self,
        ttl_seconds: float = 300.0,
        clock=time.monotonic,
    ) -> None:
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")

        self.ttl_seconds = float(ttl_seconds)
        self._clock = clock
        self._items: dict[str, _CacheEntry] = {}

    def get(
        self,
        key: str,
        *,
        allow_stale: bool = False,
    ):
        entry = self._items.get(key)

        if entry is None:
            return None

        age = self._clock() - entry.stored_at

        if age <= self.ttl_seconds or allow_stale:
            return entry.value

        return None

    def set(self, key: str, value) -> None:
        self._items[key] = _CacheEntry(
            value=value,
            stored_at=self._clock(),
        )

    def clear(self) -> None:
        self._items.clear()
