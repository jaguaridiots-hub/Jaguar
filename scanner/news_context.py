from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from typing import Any

from news.models import NewsItem, NewsSnapshot
from scanner.intelligence import ScannerAlert


_SYMBOL_SUFFIXES = (
    "USDT",
    "USD",
)

_ASSET_ALIASES: dict[str, tuple[str, ...]] = {
    "BTC": ("btc", "bitcoin"),
    "ETH": ("eth", "ethereum"),
    "BNB": ("bnb", "binance coin"),
    "SOL": ("sol", "solana"),
    "XRP": ("xrp", "ripple"),
    "DOGE": ("doge", "dogecoin"),
    "ADA": ("ada", "cardano"),
    "LINK": ("link", "chainlink"),
    "AVAX": ("avax", "avalanche"),
    "XAU": ("xau", "gold"),
    "XAG": ("xag", "silver"),
}


def _base_symbol(symbol: str) -> str:
    value = str(symbol or "").strip().upper()

    if value.endswith(".NS") or value.endswith(".BO"):
        value = value.rsplit(".", 1)[0]

    for suffix in _SYMBOL_SUFFIXES:
        if value.endswith(suffix) and len(value) > len(suffix):
            value = value[: -len(suffix)]
            break

    return value


def _tokens(text: str) -> tuple[str, ...]:
    return tuple(
        token
        for token in re.findall(
            r"[A-Za-z0-9]+(?:'[A-Za-z0-9]+)?",
            str(text or "").lower(),
        )
        if token
    )


def _title_matches_asset(
    title: str,
    base_symbol: str,
) -> bool:
    normalized = str(title or "").lower()

    aliases = _ASSET_ALIASES.get(
        base_symbol,
        (base_symbol.lower(),),
    )

    for alias in aliases:
        alias = alias.strip().lower()

        if not alias:
            continue

        if " " in alias:
            if alias in normalized:
                return True
            continue

        if alias in _tokens(normalized):
            return True

    return False


def _item_relevance(
    alert: ScannerAlert,
    item: NewsItem,
) -> tuple[str, str] | None:
    alert_symbol = str(alert.symbol).strip().upper()
    item_symbol = (
        str(item.symbol).strip().upper()
        if item.symbol
        else None
    )

    if item_symbol == alert_symbol:
        return (
            "HIGH",
            "EXACT_SYMBOL_METADATA",
        )

    base = _base_symbol(alert_symbol)

    if _title_matches_asset(item.title, base):
        return (
            "MEDIUM",
            "TITLE_ASSET_MATCH",
        )

    return None


@dataclass(frozen=True)
class RelatedNewsItem:
    item_id: str
    publisher: str
    title: str
    published_at: str
    url: str
    symbol: str | None
    category: str
    source: str
    cached: bool
    relevance: str
    match_reason: str

    @classmethod
    def from_item(
        cls,
        item: NewsItem,
        *,
        relevance: str,
        match_reason: str,
    ) -> "RelatedNewsItem":
        return cls(
            item_id=item.item_id,
            publisher=item.publisher,
            title=item.title,
            published_at=item.published_at,
            url=item.url,
            symbol=item.symbol,
            category=item.category,
            source=item.source,
            cached=item.cached,
            relevance=relevance,
            match_reason=match_reason,
        )

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
            "relevance": self.relevance,
            "match_reason": self.match_reason,
        }


@dataclass(frozen=True)
class ScannerAlertNewsContext:
    alert: ScannerAlert
    news_status: str
    news_provider: str
    news_cached: bool
    related_items: tuple[RelatedNewsItem, ...] = field(
        default_factory=tuple
    )
    correlation: str = "NO_MATCH"
    context_summary: str = ""
    context_fingerprint: str = ""
    authority: str = "SCANNER_ALERT_NEWS_CONTEXT_ONLY"

    def to_dict(self) -> dict[str, Any]:
        return {
            "alert": self.alert.to_dict(),
            "news_status": self.news_status,
            "news_provider": self.news_provider,
            "news_cached": self.news_cached,
            "related_items": [
                item.to_dict()
                for item in self.related_items
            ],
            "correlation": self.correlation,
            "context_summary": self.context_summary,
            "context_fingerprint": self.context_fingerprint,
            "authority": self.authority,
        }


class ScannerNewsContext:
    """
    Pure correlation layer between a ScannerAlert and NewsSnapshot.

    News is contextual only. This class does not alter the alert,
    calculate trading scores, persist data, or invoke execution.
    """

    def correlate(
        self,
        alert: ScannerAlert,
        news: NewsSnapshot,
        *,
        limit: int = 5,
    ) -> ScannerAlertNewsContext:
        if not isinstance(alert, ScannerAlert):
            raise TypeError("alert must be ScannerAlert")

        if not isinstance(news, NewsSnapshot):
            raise TypeError("news must be NewsSnapshot")

        limit = max(1, min(int(limit), 20))

        matches: list[
            tuple[
                NewsItem,
                str,
                str,
            ]
        ] = []

        for item in news.items:
            relevance = _item_relevance(
                alert,
                item,
            )

            if relevance is None:
                continue

            matches.append(
                (
                    item,
                    relevance[0],
                    relevance[1],
                )
            )

        relevance_rank = {
            "HIGH": 0,
            "MEDIUM": 1,
        }

        # Stable two-pass ordering:
        # 1. newest publication first;
        # 2. HIGH relevance before MEDIUM relevance.
        matches.sort(
            key=lambda row: (
                str(row[0].published_at or ""),
                str(row[0].item_id or ""),
            ),
            reverse=True,
        )

        matches.sort(
            key=lambda row: relevance_rank.get(row[1], 99),
            reverse=False,
        )

        matches = matches[:limit]

        related_items = tuple(
            RelatedNewsItem.from_item(
                item,
                relevance=relevance,
                match_reason=reason,
            )
            for item, relevance, reason in matches
        )

        if not related_items:
            correlation = "NO_MATCH"
            context_summary = (
                f"No symbol-related news matched "
                f"{alert.symbol}."
            )
        elif any(
            item.relevance == "HIGH"
            for item in related_items
        ):
            correlation = "SYMBOL_MATCH"
            context_summary = (
                f"{len(related_items)} related news item(s) "
                f"found with exact symbol context for "
                f"{alert.symbol}."
            )
        else:
            correlation = "TITLE_MATCH"
            context_summary = (
                f"{len(related_items)} related news item(s) "
                f"found from asset-title matching for "
                f"{alert.symbol}."
            )

        fingerprint_payload = {
            "alert_fingerprint": alert.fingerprint,
            "news_status": news.status,
            "news_provider": news.provider,
            "news_cached": bool(news.cached),
            "related_items": [
                {
                    "id": item.item_id,
                    "published_at": item.published_at,
                    "relevance": item.relevance,
                    "match_reason": item.match_reason,
                }
                for item in related_items
            ],
        }

        encoded = json.dumps(
            fingerprint_payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        context_fingerprint = hashlib.sha256(
            encoded
        ).hexdigest()

        return ScannerAlertNewsContext(
            alert=alert,
            news_status=str(news.status).upper(),
            news_provider=str(news.provider),
            news_cached=bool(news.cached),
            related_items=related_items,
            correlation=correlation,
            context_summary=context_summary,
            context_fingerprint=context_fingerprint,
        )
