"""R22 deterministic ScannerAlert / NewsSnapshot correlation tests."""

from __future__ import annotations

from news.models import NewsItem, NewsSnapshot
from scanner.engine import ScannerEngine
from scanner.intelligence import ScannerIntelligence
from scanner.news_context import (
    ScannerAlertNewsContext,
    ScannerNewsContext,
)


NOW_MS = 1_800_000_000_000


def _candles(
    direction: str = "BULLISH",
    count: int = 260,
):
    candles = []
    price = 100.0
    interval_ms = 15 * 60 * 1000

    first_time = (
        NOW_MS
        - ((count - 1) * interval_ms)
        - interval_ms
    )

    bullish = direction == "BULLISH"

    for index in range(count):
        candle_time = first_time + (
            index * interval_ms
        )

        if bullish:
            open_price = price
            close = price + 0.75
            low = open_price - 0.10
            high = close + 0.20
        else:
            open_price = price
            close = price - 0.75
            high = open_price + 0.10
            low = close - 0.20

        candles.append(
            {
                "time": candle_time,
                "close_time": candle_time + interval_ms,
                "open": open_price,
                "high": high,
                "low": low,
                "close": close,
                "volume": 1000.0 + (index % 12) * 80.0,
            }
        )

        price = close

    for item in candles[-3:]:
        item["volume"] = 3000.0

    return candles


def _alert(
    symbol: str = "BTCUSDT",
):
    candidate = ScannerEngine().scan(
        symbol,
        "15m",
        {
            "15m": _candles(),
            "1h": _candles(),
            "4h": _candles(),
            "1d": _candles(),
        },
        now_ms=NOW_MS,
    )

    return ScannerIntelligence().enrich(
        candidate
    )


def _news(
    *,
    items=(),
    status="CURRENT",
    provider="TEST",
    cached=False,
):
    return NewsSnapshot(
        status=status,
        provider=provider,
        symbol=None,
        category="MARKET",
        items=tuple(items),
        cached=cached,
        fetched_at="2026-01-01T00:00:00+00:00",
        error=None,
    )


def _item(
    *,
    item_id: str,
    title: str,
    symbol: str | None = None,
    published_at: str = "2026-09-24T10:00:00+00:00",
):
    return NewsItem(
        item_id=item_id,
        publisher="TEST",
        title=title,
        published_at=published_at,
        url=f"https://example.com/{item_id}",
        symbol=symbol,
        category="MARKET",
        source="TEST",
        cached=False,
    )


def test_context_model_is_canonical():
    context = ScannerNewsContext().correlate(
        _alert(),
        _news(),
    )

    assert isinstance(
        context,
        ScannerAlertNewsContext,
    )

    assert (
        context.authority
        == "SCANNER_ALERT_NEWS_CONTEXT_ONLY"
    )


def test_exact_symbol_metadata_is_high_relevance():
    context = ScannerNewsContext().correlate(
        _alert("BTCUSDT"),
        _news(
            items=(
                _item(
                    item_id="n1",
                    title="Market update",
                    symbol="BTCUSDT",
                ),
            )
        ),
    )

    assert context.correlation == "SYMBOL_MATCH"
    assert len(context.related_items) == 1
    assert (
        context.related_items[0].relevance
        == "HIGH"
    )
    assert (
        context.related_items[0].match_reason
        == "EXACT_SYMBOL_METADATA"
    )


def test_asset_title_match_is_medium_relevance():
    context = ScannerNewsContext().correlate(
        _alert("BTCUSDT"),
        _news(
            items=(
                _item(
                    item_id="n2",
                    title="Bitcoin market demand rises",
                ),
            )
        ),
    )

    assert context.correlation == "TITLE_MATCH"
    assert len(context.related_items) == 1
    assert (
        context.related_items[0].relevance
        == "MEDIUM"
    )
    assert (
        context.related_items[0].match_reason
        == "TITLE_ASSET_MATCH"
    )


def test_unrelated_news_is_not_correlated():
    context = ScannerNewsContext().correlate(
        _alert("BTCUSDT"),
        _news(
            items=(
                _item(
                    item_id="n3",
                    title="European equities rebound",
                ),
            )
        ),
    )

    assert context.correlation == "NO_MATCH"
    assert context.related_items == ()


def test_exact_symbol_match_has_precedence():
    context = ScannerNewsContext().correlate(
        _alert("BTCUSDT"),
        _news(
            items=(
                _item(
                    item_id="title",
                    title="Bitcoin market update",
                ),
                _item(
                    item_id="exact",
                    title="Market update",
                    symbol="BTCUSDT",
                ),
            )
        ),
    )

    assert context.related_items[0].item_id == "exact"
    assert context.related_items[0].relevance == "HIGH"


def test_limit_is_respected():
    context = ScannerNewsContext().correlate(
        _alert("BTCUSDT"),
        _news(
            items=tuple(
                _item(
                    item_id=f"n{index}",
                    title=f"Bitcoin update {index}",
                )
                for index in range(10)
            )
        ),
        limit=3,
    )

    assert len(context.related_items) == 3


def test_result_is_deterministic():
    alert = _alert("ETHUSDT")

    news = _news(
        items=(
            _item(
                item_id="b",
                title="Ethereum demand update",
                published_at="2026-09-24T11:00:00+00:00",
            ),
            _item(
                item_id="a",
                title="Ethereum network update",
                published_at="2026-09-24T12:00:00+00:00",
            ),
        )
    )

    first = ScannerNewsContext().correlate(
        alert,
        news,
    )

    second = ScannerNewsContext().correlate(
        alert,
        news,
    )

    assert first.to_dict() == second.to_dict()


def test_newer_title_match_is_ordered_first():
    context = ScannerNewsContext().correlate(
        _alert("ETHUSDT"),
        _news(
            items=(
                _item(
                    item_id="old",
                    title="Ethereum older update",
                    published_at="2026-09-24T09:00:00+00:00",
                ),
                _item(
                    item_id="new",
                    title="Ethereum newer update",
                    published_at="2026-09-24T12:00:00+00:00",
                ),
            )
        ),
    )

    assert (
        [item.item_id for item in context.related_items]
        == ["new", "old"]
    )


def test_news_status_is_preserved():
    context = ScannerNewsContext().correlate(
        _alert(),
        _news(
            status="CACHED",
            provider="CACHE",
            cached=True,
        ),
    )

    assert context.news_status == "CACHED"
    assert context.news_provider == "CACHE"
    assert context.news_cached is True


def test_context_does_not_mutate_alert():
    alert = _alert()
    before = alert.to_dict()

    ScannerNewsContext().correlate(
        alert,
        _news(
            items=(
                _item(
                    item_id="n4",
                    title="Bitcoin update",
                ),
            )
        ),
    )

    assert alert.to_dict() == before


def test_context_fingerprint_changes_when_news_changes():
    alert = _alert()

    first = ScannerNewsContext().correlate(
        alert,
        _news(
            items=(
                _item(
                    item_id="n5",
                    title="Bitcoin update A",
                ),
            )
        ),
    )

    second = ScannerNewsContext().correlate(
        alert,
        _news(
            items=(
                _item(
                    item_id="n6",
                    title="Bitcoin update B",
                ),
            )
        ),
    )

    assert (
        first.context_fingerprint
        != second.context_fingerprint
    )


def test_no_match_has_explainable_summary():
    context = ScannerNewsContext().correlate(
        _alert("SOLUSDT"),
        _news(
            items=(
                _item(
                    item_id="n7",
                    title="US bond yields move",
                ),
            )
        ),
    )

    assert context.correlation == "NO_MATCH"
    assert "No symbol-related news matched" in (
        context.context_summary
    )


def test_related_news_serialization_is_json_safe():
    import json

    context = ScannerNewsContext().correlate(
        _alert("BTCUSDT"),
        _news(
            items=(
                _item(
                    item_id="n8",
                    title="Bitcoin market update",
                ),
            )
        ),
    )

    encoded = json.dumps(
        context.to_dict()
    )

    assert isinstance(encoded, str)
    assert (
        "SCANNER_ALERT_NEWS_CONTEXT_ONLY"
        in encoded
    )


def test_context_layer_has_no_trading_authority():
    from pathlib import Path

    source = Path(
        "scanner/news_context.py"
    ).read_text(encoding="utf-8").lower()

    forbidden = (
        "tradeplanner",
        "riskmanager",
        "executionconfirmation",
        "executiongateway",
        "execution_intent",
        "place_order",
        "submit_order",
        "research.database",
        "state.decision",
        "state.trade",
        "state.risk",
        "state.execution",
    )

    for term in forbidden:
        assert term not in source, term


def test_context_layer_has_no_randomness():
    from pathlib import Path

    source = Path(
        "scanner/news_context.py"
    ).read_text(encoding="utf-8").lower()

    assert "random" not in source


def test_context_does_not_modify_news_snapshot():
    news = _news(
        items=(
            _item(
                item_id="n9",
                title="Bitcoin update",
            ),
        )
    )

    before = news.to_dict()

    ScannerNewsContext().correlate(
        _alert(),
        news,
    )

    assert news.to_dict() == before
