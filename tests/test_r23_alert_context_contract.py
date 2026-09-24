"""R23 scanner-alert news-context service/API/UI contract tests."""

from __future__ import annotations

import json
from pathlib import Path

from news.models import NewsItem, NewsSnapshot
from scanner.alerts import ScannerAlertSnapshot
from scanner.engine import ScannerEngine
from scanner.intelligence import ScannerIntelligence
from scanner.news_context import ScannerNewsContext


SOURCE_API = Path("api.py").read_text(encoding="utf-8")
SOURCE_UI = Path(
    "dashboard/command_center_v3.py"
).read_text(encoding="utf-8")


def _r23_service():
    from scanner.alert_context import ScannerAlertContextService

    return ScannerAlertContextService


def _candles():
    candles = []
    price = 100.0
    interval_ms = 15 * 60 * 1000
    now_ms = 1_800_000_000_000
    count = 260

    first_time = (
        now_ms
        - ((count - 1) * interval_ms)
        - interval_ms
    )

    for index in range(count):
        candle_time = first_time + (
            index * interval_ms
        )

        open_price = price
        close = price + 0.75
        low = open_price - 0.10
        high = close + 0.20

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


def _alert(symbol="BTCUSDT"):
    candidate = ScannerEngine().scan(
        symbol,
        "15m",
        {
            "15m": _candles(),
        },
        now_ms=1_800_000_000_000,
    )

    return ScannerIntelligence().enrich(candidate)


def _news(
    symbol="BTCUSDT",
    *,
    title="Bitcoin momentum remains strong",
):
    return NewsSnapshot(
        status="CURRENT",
        provider="TEST",
        symbol=symbol,
        category="MARKET",
        items=(
            NewsItem(
                item_id="news-1",
                publisher="Test Publisher",
                title=title,
                published_at="2026-09-24T10:00:00+00:00",
                url="https://example.com/news-1",
                symbol=symbol,
                category="MARKET",
                source="TEST",
                cached=False,
            ),
        ),
        cached=False,
        fetched_at="2026-09-24T10:01:00+00:00",
        error=None,
    )


class StubAlerts:
    def __init__(self, snapshot):
        self.snapshot = snapshot
        self.calls = []

    def scan_watchlist(
        self,
        *,
        symbols=None,
        now_ms=None,
    ):
        self.calls.append(
            (symbols, now_ms)
        )
        return self.snapshot


class StubNews:
    def __init__(self, snapshots):
        self.snapshots = snapshots
        self.calls = []

    def get_news(
        self,
        *,
        symbol=None,
        category="MARKET",
        limit=20,
        refresh=False,
    ):
        self.calls.append(
            (
                symbol,
                category,
                limit,
                refresh,
            )
        )
        return self.snapshots[symbol]


def _service(alerts, news):
    return _r23_service()(
        alerts=alerts,
        news=news,
        context=ScannerNewsContext(),
    )


def test_context_snapshot_is_canonical():
    service_cls = _r23_service()

    assert hasattr(
        service_cls,
        "scan_watchlist",
    )


def test_service_returns_one_context_per_alert():
    alert = _alert()

    alerts = StubAlerts(
        ScannerAlertSnapshot(
            status="CURRENT",
            generated_at=1_800_000_000_000,
            scanned_symbols=1,
            candidate_count=1,
            alert_count=1,
            alerts=(alert,),
            errors=(),
        )
    )

    news = StubNews(
        {
            "BTCUSDT": _news(),
        }
    )

    snapshot = _service(
        alerts,
        news,
    ).scan_watchlist(
        symbols=("BTCUSDT",),
        now_ms=123,
    )

    assert snapshot.status == "CURRENT"
    assert snapshot.context_count == 1
    assert len(snapshot.contexts) == 1
    assert snapshot.contexts[0].alert == alert


def test_service_passes_scan_arguments():
    alerts = StubAlerts(
        ScannerAlertSnapshot(
            status="CURRENT",
            generated_at=123,
            scanned_symbols=0,
            candidate_count=0,
            alert_count=0,
            alerts=(),
            errors=(),
        )
    )

    news = StubNews({})

    _service(
        alerts,
        news,
    ).scan_watchlist(
        symbols=("ETHUSDT",),
        now_ms=123,
    )

    assert alerts.calls == [
        (("ETHUSDT",), 123)
    ]


def test_service_fetches_news_once_per_unique_symbol():
    first = _alert("BTCUSDT")
    second = _alert("BTCUSDT")

    alerts = StubAlerts(
        ScannerAlertSnapshot(
            status="CURRENT",
            generated_at=123,
            scanned_symbols=1,
            candidate_count=2,
            alert_count=2,
            alerts=(
                first,
                second,
            ),
            errors=(),
        )
    )

    news = StubNews(
        {
            "BTCUSDT": _news(),
        }
    )

    snapshot = _service(
        alerts,
        news,
    ).scan_watchlist()

    assert snapshot.context_count == 2

    assert news.calls == [
        (
            "BTCUSDT",
            "MARKET",
            5,
            False,
        )
    ]


def test_service_passes_news_refresh():
    alert = _alert()

    alerts = StubAlerts(
        ScannerAlertSnapshot(
            status="CURRENT",
            generated_at=123,
            scanned_symbols=1,
            candidate_count=1,
            alert_count=1,
            alerts=(alert,),
            errors=(),
        )
    )

    news = StubNews(
        {
            "BTCUSDT": _news(),
        }
    )

    _service(
        alerts,
        news,
    ).scan_watchlist(
        refresh_news=True,
    )

    assert news.calls == [
        (
            "BTCUSDT",
            "MARKET",
            5,
            True,
        )
    ]


def test_service_preserves_alert_errors():
    alerts = StubAlerts(
        ScannerAlertSnapshot(
            status="DEGRADED",
            generated_at=123,
            scanned_symbols=1,
            candidate_count=0,
            alert_count=0,
            alerts=(),
            errors=(
                {
                    "symbol": "BTCUSDT",
                    "timeframe": "1h",
                    "error": "provider unavailable",
                },
            ),
        )
    )

    news = StubNews({})

    snapshot = _service(
        alerts,
        news,
    ).scan_watchlist()

    assert snapshot.status == "DEGRADED"
    assert snapshot.context_count == 0
    assert snapshot.errors[0]["error"] == (
        "provider unavailable"
    )


def test_service_is_json_safe():
    alert = _alert()

    alerts = StubAlerts(
        ScannerAlertSnapshot(
            status="CURRENT",
            generated_at=123,
            scanned_symbols=1,
            candidate_count=1,
            alert_count=1,
            alerts=(alert,),
            errors=(),
        )
    )

    news = StubNews(
        {
            "BTCUSDT": _news(),
        }
    )

    encoded = json.dumps(
        _service(
            alerts,
            news,
        ).scan_watchlist().to_dict()
    )

    assert '"context_count": 1' in encoded


def test_service_does_not_mutate_alert_or_news():
    alert = _alert()
    news_snapshot = _news()

    alert_before = alert.to_dict()
    news_before = news_snapshot.to_dict()

    alerts = StubAlerts(
        ScannerAlertSnapshot(
            status="CURRENT",
            generated_at=123,
            scanned_symbols=1,
            candidate_count=1,
            alert_count=1,
            alerts=(alert,),
            errors=(),
        )
    )

    news = StubNews(
        {
            "BTCUSDT": news_snapshot,
        }
    )

    _service(
        alerts,
        news,
    ).scan_watchlist()

    assert alert.to_dict() == alert_before
    assert news_snapshot.to_dict() == news_before


def test_service_has_no_trading_authority():
    source = (
        Path("scanner/alert_context.py")
        .read_text(encoding="utf-8")
        .lower()
    )

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


def test_api_imports_context_service():
    assert (
        "from scanner.alert_context import "
        "ScannerAlertContextService"
        in SOURCE_API
    )


def test_api_constructs_context_service():
    assert (
        "scanner_alert_context_service = "
        "ScannerAlertContextService("
        in SOURCE_API
    )


def test_api_context_route_exists():
    assert (
        '@app.get("/scanner/alert-context"'
        in SOURCE_API
    )


def test_api_context_route_exposes_filters():
    start = SOURCE_API.index(
        '@app.get("/scanner/alert-context"'
    )

    block = SOURCE_API[start:]

    assert (
        "symbol: str | None = None"
        in block
    )

    assert "limit: int = 5" in block
    assert "refresh: bool = False" in block


def test_api_context_route_validates_limit():
    start = SOURCE_API.index(
        '@app.get("/scanner/alert-context"'
    )

    block = SOURCE_API[start:]

    assert (
        "limit < 1 or limit > 20"
        in block
    )

    assert (
        'detail="limit must be between 1 and 20"'
        in block
    )


def test_api_context_route_serializes_snapshot():
    start = SOURCE_API.index(
        '@app.get("/scanner/alert-context"'
    )

    block = SOURCE_API[start:]

    assert "snapshot.to_dict()" in block


def test_api_context_route_has_no_trading_authority():
    start = SOURCE_API.index(
        '@app.get("/scanner/alert-context"'
    )

    block = SOURCE_API[start:].lower()

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
        assert term not in block, term


def _ui_blocks():
    result = []

    for start_marker, end_marker in (
        (
            "/* R23_SCANNER_ALERT_CONTEXT_UI_START */",
            "/* R23_SCANNER_ALERT_CONTEXT_UI_END */",
        ),
        (
            "<!-- R23_SCANNER_ALERT_CONTEXT_UI_START -->",
            "<!-- R23_SCANNER_ALERT_CONTEXT_UI_END -->",
        ),
    ):
        cursor = 0

        while True:
            start = SOURCE_UI.find(
                start_marker,
                cursor,
            )

            if start < 0:
                break

            end = SOURCE_UI.find(
                end_marker,
                start,
            )

            assert end >= 0

            result.append(
                SOURCE_UI[
                    start:end
                ]
            )

            cursor = (
                end + len(end_marker)
            )

    # Canonical presentation order: CSS -> HTML -> JS.
    result.sort(
        key=lambda block: (
            0
            if ".scanner-alert-context-card" in block
            else 1
            if "<details" in block
            else 2
        )
    )

    return result


def test_r23_ui_has_css_html_js_blocks():
    blocks = _ui_blocks()

    assert len(blocks) == 3

    assert (
        ".scanner-alert-context-card"
        in blocks[0]
    )

    assert "<details" in blocks[1]

    assert (
        "function loadScannerAlertContext"
        in blocks[2]
    )


def test_r23_ui_has_controls_and_output():
    blocks = "\n".join(_ui_blocks())

    for term in (
        "scannerAlertContextSymbol",
        "scannerAlertContextScanSymbol",
        "scannerAlertContextScanWatchlist",
        "scannerAlertContextStatus",
        "scannerAlertContextList",
    ):
        assert term in blocks


def test_r23_ui_calls_context_api():
    blocks = "\n".join(_ui_blocks())

    assert (
        "/scanner/alert-context"
        in blocks
    )

    assert "fetch(" in blocks


def test_r23_ui_renders_news_context():
    blocks = "\n".join(_ui_blocks())

    assert "const alert=context.alert||{}" in blocks

    for term in (
        "alert.symbol",
        "alert.direction",
        "alert.setup",
        "alert.priority",
        "context.news_status",
        "context.news_provider",
        "context.news_cached",
        "context.context_summary",
        "context.related_items",
        "item.publisher",
        "item.title",
        "item.published_at",
        "item.relevance",
        "item.match_reason",
    ):
        assert term in blocks


def test_r23_ui_is_explicit_scan_only():
    blocks = "\n".join(_ui_blocks())

    init_start = blocks.index(
        "function initScannerAlertContextControls"
    )

    before_init = blocks[:init_start]
    after_init = blocks[init_start:]

    declaration = (
        "async function loadScannerAlertContext("
    )

    assert (
        "loadScannerAlertContext("
        not in before_init.replace(
            declaration,
            "",
            1,
        )
    )

    assert (
        "renderScannerAlertContext();"
        in after_init
    )

    symbol_handler = after_init.index(
        "scanSymbolEl.onclick"
    )

    watchlist_handler = after_init.index(
        "scanWatchlistEl.onclick"
    )

    symbol_call = after_init.index(
        "loadScannerAlertContext(",
        symbol_handler,
    )

    watchlist_call = after_init.index(
        "loadScannerAlertContext(",
        watchlist_handler,
    )

    assert symbol_handler < symbol_call
    assert watchlist_handler < watchlist_call


def test_r23_ui_has_context_boundary():
    blocks = "\n".join(_ui_blocks())

    assert (
        "CONTEXT ONLY"
        in blocks
    )

    assert (
        "READ-ONLY"
        in blocks
    )


def test_r23_ui_is_read_only_context():
    blocks = "\n".join(_ui_blocks()).lower()

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
        assert term not in blocks, term


def test_r21_and_r18_ui_remain():
    assert (
        "R21_SCANNER_ALERT_UI_START"
        in SOURCE_UI
    )

    assert (
        "R21_SCANNER_ALERT_UI_END"
        in SOURCE_UI
    )

    assert (
        "R18_NEWS_UI_START"
        in SOURCE_UI
    )

    assert (
        "R18_NEWS_UI_END"
        in SOURCE_UI
    )


def test_r18_news_api_remains():
    assert (
        '@app.get("/news"'
        in SOURCE_API
    )

    assert (
        '@app.get("/scanner/alerts"'
        in SOURCE_API
    )
