"""33C-R18 dependency-free news contracts."""

from __future__ import annotations

import io
import json
from email.utils import format_datetime
from datetime import datetime, timezone

from news.cache import NewsCache
from news.cnbc import CNBCNewsProvider
from news.models import NewsItem, NewsSnapshot
from news.normalizer import (
    make_item_id,
    matches_symbol,
    parse_timestamp,
    valid_item,
)
from news.provider import NewsQuery, NewsProviderError
from news.service import JaguarNewsService
from news.yahoo import YahooFinanceNewsProvider


class FakeResponse:
    def __init__(self, payload: bytes):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.payload


class FakeProvider:
    def __init__(self, name="FAKE", items=None, error=None):
        self.name = name
        self.items = list(items or [])
        self.error = error
        self.calls = 0

    def fetch(self, query):
        self.calls += 1
        if self.error:
            raise self.error
        return self.items[:query.limit]


def sample_item(symbol="BTCUSDT"):
    return NewsItem(
        item_id=make_item_id(
            "Bitcoin market update",
            "https://example.com/a",
        ),
        publisher="CNBC",
        title="Bitcoin market update",
        published_at=datetime.now(
            timezone.utc
        ).isoformat(),
        url="https://example.com/a",
        symbol=symbol,
        category="CRYPTO",
        source="CNBC",
    )


def test_news_item_contract():
    item = sample_item()
    data = item.to_dict()

    assert data["publisher"] == "CNBC"
    assert data["symbol"] == "BTCUSDT"
    assert data["category"] == "CRYPTO"
    assert data["cached"] is False


def test_timestamp_normalization():
    raw = format_datetime(
        datetime.now(timezone.utc)
    )

    normalized = parse_timestamp(raw)

    assert normalized is not None
    assert normalized.endswith("+00:00")


def test_malformed_items_are_rejected():
    assert valid_item(
        title="",
        url="https://example.com",
        published_at=datetime.now(timezone.utc).isoformat(),
    ) is None

    assert valid_item(
        title="Valid title",
        url="not-a-url",
        published_at=datetime.now(timezone.utc).isoformat(),
    ) is None


def test_symbol_matching():
    assert matches_symbol(
        "Bitcoin falls as crypto market reacts",
        "BTCUSDT",
    )

    assert not matches_symbol(
        "Apple reports earnings",
        "BTCUSDT",
    )


def test_cnbc_normalizes_rss():
    published = format_datetime(
        datetime.now(timezone.utc)
    )

    rss = f"""
    <rss version="2.0">
      <channel>
        <item>
          <title>Bitcoin market update</title>
          <link>https://www.cnbc.com/article/1</link>
          <pubDate>{published}</pubDate>
        </item>
        <item>
          <title>Malformed</title>
          <link>bad</link>
          <pubDate>{published}</pubDate>
        </item>
      </channel>
    </rss>
    """.encode()

    provider = CNBCNewsProvider(
        feed_url="https://example.test/feed",
        opener=lambda request, timeout: FakeResponse(rss),
    )

    items = provider.fetch(
        NewsQuery(
            symbol="BTCUSDT",
            category="CRYPTO",
            limit=10,
        )
    )

    assert len(items) == 1
    assert items[0].publisher == "CNBC"
    assert items[0].symbol == "BTCUSDT"


def test_yahoo_normalizes_json():
    published = int(datetime.now(timezone.utc).timestamp())

    payload = {
        "news": [
            {
                "uuid": "abc",
                "title": "Bitcoin market update",
                "publisher": "Yahoo Finance",
                "link": "https://finance.yahoo.com/news/a",
                "providerPublishTime": published,
                "relatedTickers": ["BTC-USD"],
            }
        ]
    }

    raw = json.dumps(payload).encode()

    provider = YahooFinanceNewsProvider(
        base_url="https://example.test/search",
        opener=lambda request, timeout: FakeResponse(raw),
    )

    items = provider.fetch(
        NewsQuery(
            symbol="BTCUSDT",
            category="CRYPTO",
            limit=10,
        )
    )

    assert len(items) == 1
    assert items[0].publisher == "Yahoo Finance"


def test_provider_failure_falls_back():
    primary = FakeProvider(
        name="CNBC",
        error=RuntimeError("timeout"),
    )
    fallback = FakeProvider(
        name="Yahoo Finance",
        items=[sample_item()],
    )

    service = JaguarNewsService(
        primary=primary,
        fallback=fallback,
    )

    snapshot = service.get_news(
        symbol="BTCUSDT",
        category="CRYPTO",
        refresh=True,
    )

    assert snapshot.status == "CURRENT"
    assert snapshot.provider == "Yahoo Finance"
    assert len(snapshot.items) == 1
    assert primary.calls == 1
    assert fallback.calls == 1


def test_cached_news_fallback():
    primary = FakeProvider(
        name="CNBC",
        items=[sample_item()],
    )
    fallback = FakeProvider(
        name="Yahoo Finance",
        error=RuntimeError("offline"),
    )

    cache = NewsCache()

    service = JaguarNewsService(
        primary=primary,
        fallback=fallback,
        cache=cache,
    )

    first = service.get_news(
        symbol="BTCUSDT",
        category="CRYPTO",
        refresh=True,
    )

    assert first.status == "CURRENT"

    failing_primary = FakeProvider(
        name="CNBC",
        error=RuntimeError("offline"),
    )

    service = JaguarNewsService(
        primary=failing_primary,
        fallback=fallback,
        cache=cache,
    )

    cached = service.get_news(
        symbol="BTCUSDT",
        category="CRYPTO",
        refresh=True,
    )

    assert cached.status == "CACHED"
    assert cached.cached is True
    assert cached.items[0].cached is True


def test_all_providers_failure_returns_unavailable():
    primary = FakeProvider(
        name="CNBC",
        error=RuntimeError("cnbc failed"),
    )
    fallback = FakeProvider(
        name="Yahoo Finance",
        error=RuntimeError("yahoo failed"),
    )

    service = JaguarNewsService(
        primary=primary,
        fallback=fallback,
    )

    snapshot = service.get_news(
        symbol="BTCUSDT",
        category="CRYPTO",
        refresh=True,
    )

    assert snapshot.status == "UNAVAILABLE"
    assert snapshot.provider == "NONE"
    assert snapshot.items == ()


def test_snapshot_contract():
    snapshot = NewsSnapshot(
        status="CURRENT",
        provider="CNBC",
        symbol="BTCUSDT",
        category="CRYPTO",
        items=(sample_item(),),
        cached=False,
        fetched_at=datetime.now(timezone.utc).isoformat(),
    )

    data = snapshot.to_dict()

    assert data["status"] == "CURRENT"
    assert len(data["items"]) == 1
