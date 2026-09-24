"""R21 scanner-alert service contract tests."""

from __future__ import annotations

from scanner.alerts import ScannerAlertService
from scanner.engine import ScannerEngine
from scanner.models import ScannerCandidate, ScannerSnapshot
from scanner.intelligence import ScannerIntelligence


class StubScanner:
    def __init__(self, snapshot):
        self.snapshot = snapshot
        self.calls = []

    def scan_watchlist(self, *, symbols=None, now_ms=None):
        self.calls.append(
            (symbols, now_ms)
        )
        return self.snapshot


def _candidate():
    return ScannerEngine().scan(
        "BTCUSDT",
        "15m",
        {
            "15m": _candles(),
        },
        now_ms=1_800_000_000_000,
    )


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


def test_service_returns_snapshot():
    candidate = _candidate()

    scanner = StubScanner(
        ScannerSnapshot(
            status="CURRENT",
            generated_at=1_800_000_000_000,
            scanned_symbols=1,
            candidate_count=1,
            candidates=(candidate,),
            errors=(),
        )
    )

    service = ScannerAlertService(
        scanner=scanner,
        intelligence=ScannerIntelligence(),
    )

    snapshot = service.scan_watchlist(
        symbols=("BTCUSDT",),
        now_ms=1_800_000_000_000,
    )

    assert snapshot.status == "CURRENT"
    assert snapshot.scanned_symbols == 1
    assert snapshot.candidate_count == 1
    assert snapshot.alert_count == 1
    assert len(snapshot.alerts) == 1


def test_service_passes_scan_arguments():
    scanner = StubScanner(
        ScannerSnapshot(
            status="CURRENT",
            generated_at=123,
            scanned_symbols=0,
            candidate_count=0,
            candidates=(),
            errors=(),
        )
    )

    service = ScannerAlertService(
        scanner=scanner,
        intelligence=ScannerIntelligence(),
    )

    service.scan_watchlist(
        symbols=("ETHUSDT",),
        now_ms=123,
    )

    assert scanner.calls == [
        (("ETHUSDT",), 123)
    ]


def test_service_preserves_errors():
    scanner = StubScanner(
        ScannerSnapshot(
            status="DEGRADED",
            generated_at=123,
            scanned_symbols=1,
            candidate_count=0,
            candidates=(),
            errors=(
                {
                    "symbol": "BTCUSDT",
                    "timeframe": "1h",
                    "error": "provider unavailable",
                },
            ),
        )
    )

    snapshot = ScannerAlertService(
        scanner=scanner,
        intelligence=ScannerIntelligence(),
    ).scan_watchlist()

    assert snapshot.status == "DEGRADED"
    assert snapshot.alert_count == 0
    assert snapshot.errors[0]["error"] == (
        "provider unavailable"
    )


def test_service_serialization_is_json_safe():
    import json

    candidate = _candidate()

    scanner = StubScanner(
        ScannerSnapshot(
            status="CURRENT",
            generated_at=1_800_000_000_000,
            scanned_symbols=1,
            candidate_count=1,
            candidates=(candidate,),
            errors=(),
        )
    )

    snapshot = ScannerAlertService(
        scanner=scanner,
    ).scan_watchlist()

    encoded = json.dumps(
        snapshot.to_dict()
    )

    assert '"alert_count": 1' in encoded


def test_service_has_no_trading_authority():
    source = (
        __import__(
            "pathlib"
        )
        .Path("scanner/alerts.py")
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
