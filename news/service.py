from __future__ import annotations

from datetime import datetime, timezone

from news.cache import NewsCache
from news.cnbc import CNBCNewsProvider
from news.models import NewsItem, NewsSnapshot
from news.provider import NewsProvider, NewsProviderError, NewsQuery
from news.yahoo import YahooFinanceNewsProvider


class JaguarNewsService:
    """
    Read-only news aggregation service.

    Provider order:
        CNBC -> Yahoo Finance -> cached snapshot
    """

    def __init__(
        self,
        primary: NewsProvider | None = None,
        fallback: NewsProvider | None = None,
        cache: NewsCache | None = None,
    ) -> None:
        self.primary = primary or CNBCNewsProvider()
        self.fallback = fallback or YahooFinanceNewsProvider()
        self.cache = cache or NewsCache()

    @staticmethod
    def _key(
        symbol: str | None,
        category: str,
        limit: int,
    ) -> str:
        return "|".join(
            [
                (symbol or "").upper(),
                category.upper(),
                str(limit),
            ]
        )

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _deduplicate(
        items: list[NewsItem],
        limit: int,
    ) -> list[NewsItem]:
        result: list[NewsItem] = []
        seen: set[str] = set()

        for item in items:
            fingerprint = (
                item.url
                or f"{item.publisher}|{item.title}"
            )

            if fingerprint in seen:
                continue

            seen.add(fingerprint)
            result.append(item)

            if len(result) >= limit:
                break

        return result

    def get_news(
        self,
        *,
        symbol: str | None = None,
        category: str = "MARKET",
        limit: int = 20,
        refresh: bool = False,
    ) -> NewsSnapshot:
        limit = max(1, min(int(limit), 50))
        symbol = symbol.strip().upper() if symbol else None
        category = str(category or "MARKET").upper().strip()

        query = NewsQuery(
            symbol=symbol,
            category=category,
            limit=limit,
        )

        key = self._key(symbol, category, limit)

        if not refresh:
            cached = self.cache.get(key)

            if isinstance(cached, NewsSnapshot):
                return cached

        failures: list[str] = []

        for provider in (self.primary, self.fallback):
            try:
                items = provider.fetch(query)
                items = self._deduplicate(items, limit)

                if not items:
                    raise NewsProviderError(
                        "Provider returned no usable items",
                        provider=provider.name,
                        kind=getattr(
                            NewsProviderError,
                            "kind",
                            None,
                        ),
                    )

                snapshot = NewsSnapshot(
                    status="CURRENT",
                    provider=provider.name,
                    symbol=symbol,
                    category=category,
                    items=tuple(items),
                    cached=False,
                    fetched_at=self._now(),
                    error=None,
                )

                self.cache.set(key, snapshot)
                return snapshot

            except Exception as exc:
                failures.append(
                    f"{getattr(provider, 'name', 'UNKNOWN')}: {exc}"
                )

        cached = self.cache.get(
            key,
            allow_stale=True,
        )

        if isinstance(cached, NewsSnapshot):
            cached_items = tuple(
                NewsItem(
                    item_id=item.item_id,
                    publisher=item.publisher,
                    title=item.title,
                    published_at=item.published_at,
                    url=item.url,
                    symbol=item.symbol,
                    category=item.category,
                    source=item.source,
                    cached=True,
                )
                for item in cached.items
            )

            return NewsSnapshot(
                status="CACHED",
                provider=cached.provider,
                symbol=symbol,
                category=category,
                items=cached_items,
                cached=True,
                fetched_at=cached.fetched_at,
                error="; ".join(failures),
            )

        return NewsSnapshot(
            status="UNAVAILABLE",
            provider="NONE",
            symbol=symbol,
            category=category,
            items=(),
            cached=False,
            fetched_at=None,
            error="; ".join(failures),
        )
