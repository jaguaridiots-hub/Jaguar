"""33C-R19 deterministic scanner contract tests."""

from __future__ import annotations

import runpy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

from scanner.engine import ScannerEngine
from scanner.models import ScannerCandidate
from scanner.service import ScannerService


def _interval_ms(interval: str) -> int:
    value = str(interval).strip().lower()

    if value.endswith("m"):
        return int(value[:-1]) * 60 * 1000

    if value.endswith("h"):
        return int(value[:-1]) * 60 * 60 * 1000

    if value.endswith("d"):
        return int(value[:-1]) * 24 * 60 * 60 * 1000

    raise ValueError(f"unsupported test interval: {interval}")


def _make_candles(
    direction: str,
    count: int = 260,
    start_price: float = 100.0,
    now_ms: int = 1_800_000_000_000,
    interval_ms: int = 15 * 60 * 1000,
    interval: str | None = None,
):
    if interval is not None:
        interval_ms = _interval_ms(interval)

    candles = []
    price = start_price

    bullish = direction == "BULLISH"

    first_time = (
        now_ms
        - ((count - 1) * interval_ms)
        - interval_ms
    )

    for index in range(count):
        candle_time = first_time + (index * interval_ms)

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

        close_time = candle_time + interval_ms

        candles.append(
            {
                "time": candle_time,
                "close_time": close_time,
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


def test_models_are_canonical():
    candidate = ScannerCandidate(
        symbol="BTCUSDT",
        timeframe="15m",
        direction="LONG",
        score=80,
        confidence=85,
        is_candidate=True,
        structure={},
        data_quality={},
    )

    data = candidate.to_dict()

    assert data["symbol"] == "BTCUSDT"
    assert data["direction"] == "LONG"
    assert data["authority"] == "SCANNER_CANDIDATE_ONLY"


def test_bullish_scan_is_deterministic():
    now_ms = 1_800_000_000_000
    candles = _make_candles("BULLISH", now_ms=now_ms)

    engine = ScannerEngine()

    first = engine.scan(
        "BTCUSDT",
        "15m",
        {
            "15m": candles,
            "1h": candles,
            "4h": candles,
            "1d": candles,
        },
        now_ms=now_ms,
    )

    second = engine.scan(
        "BTCUSDT",
        "15m",
        {
            "15m": candles,
            "1h": candles,
            "4h": candles,
            "1d": candles,
        },
        now_ms=now_ms,
    )

    assert first.to_dict() == second.to_dict()
    assert first.direction == "LONG"
    assert first.is_candidate is True
    assert first.score > 50
    assert first.confidence > 50


def test_bearish_scan_is_deterministic():
    now_ms = 1_800_000_000_000
    candles = _make_candles("BEARISH", now_ms=now_ms)

    engine = ScannerEngine()

    result = engine.scan(
        "ETHUSDT",
        "15m",
        {
            "15m": candles,
            "1h": candles,
            "4h": candles,
            "1d": candles,
        },
        now_ms=now_ms,
    )

    assert result.direction == "SHORT"
    assert result.is_candidate is True
    assert result.score < 50


def test_required_evidence_is_present():
    now_ms = 1_800_000_000_000
    candles = _make_candles("BULLISH", now_ms=now_ms)

    result = ScannerEngine().scan(
        "SOLUSDT",
        "15m",
        {
            "15m": candles,
            "1h": candles,
            "4h": candles,
            "1d": candles,
        },
        now_ms=now_ms,
    )

    names = {item.name for item in result.evidence}

    required = {
        "TREND_ALIGNMENT",
        "STRUCTURE",
        "MOMENTUM",
        "VWAP",
        "VOLUME",
        "FIBONACCI",
        "FVG",
        "LIQUIDITY",
        "MTF",
        "VOLATILITY",
        "DATA_QUALITY",
    }

    assert required.issubset(names)


def test_structure_contains_bos_and_choch_fields():
    now_ms = 1_800_000_000_000
    candles = _make_candles("BULLISH", now_ms=now_ms)

    result = ScannerEngine().scan(
        "BTCUSDT",
        "15m",
        {"15m": candles},
        now_ms=now_ms,
    )

    assert "bos" in result.structure
    assert "choch" in result.structure
    assert "trend" in result.structure


def test_missing_higher_timeframes_degrades_mtf_only():
    now_ms = 1_800_000_000_000
    candles = _make_candles("BULLISH", now_ms=now_ms)

    result = ScannerEngine().scan(
        "BTCUSDT",
        "15m",
        {"15m": candles},
        now_ms=now_ms,
    )

    mtf = next(
        item for item in result.evidence
        if item.name == "MTF"
    )

    assert mtf.signal == "NEUTRAL"
    assert mtf.score == 0


def test_stale_data_reduces_quality():
    now_ms = 1_800_000_000_000
    candles = _make_candles(
        "BULLISH",
        now_ms=now_ms - 24 * 60 * 60 * 1000,
    )

    result = ScannerEngine().scan(
        "BTCUSDT",
        "15m",
        {"15m": candles},
        now_ms=now_ms,
    )

    assert result.data_quality["freshness_ok"] is False
    assert result.data_quality["quality"] < 100


def test_insufficient_history_cannot_be_authoritative_candidate():
    now_ms = 1_800_000_000_000
    candles = _make_candles(
        "BULLISH",
        count=80,
        now_ms=now_ms,
    )

    result = ScannerEngine().scan(
        "BTCUSDT",
        "15m",
        {"15m": candles},
        now_ms=now_ms,
    )

    assert result.data_quality["quality"] <= 80
    assert result.is_candidate is False


def test_service_uses_injected_loader_and_isolates_failure():
    now_ms = 1_800_000_000_000

    calls = []

    def loader(symbol, *, interval, limit):
        calls.append((symbol, interval, limit))

        if symbol == "FAILUSDT" and interval == "4h":
            raise RuntimeError("provider unavailable")

        return _make_candles(
            "BULLISH",
            now_ms=now_ms,
        )

    service = ScannerService(
        loader=loader,
        watchlist=("BTCUSDT", "FAILUSDT"),
        timeframes=("15m", "1h", "4h", "1d"),
        limit=260,
    )

    snapshot = service.scan_watchlist(now_ms=now_ms)

    assert snapshot.status == "DEGRADED"
    assert snapshot.scanned_symbols == 2
    assert snapshot.errors
    assert calls


def test_service_sorts_candidate_strength():
    now_ms = 1_800_000_000_000

    def loader(symbol, *, interval, limit):
        if symbol == "BTCUSDT":
            return _make_candles("BULLISH", now_ms=now_ms)

        return _make_candles("BEARISH", now_ms=now_ms)

    service = ScannerService(
        loader=loader,
        watchlist=("BTCUSDT", "ETHUSDT"),
        timeframes=("15m", "1h", "4h", "1d"),
        limit=260,
    )

    snapshot = service.scan_watchlist(now_ms=now_ms)

    assert snapshot.candidate_count == 2
    assert snapshot.candidates[0].confidence >= snapshot.candidates[1].confidence


def test_scanner_does_not_touch_authority_layers():
    paths = [
        ROOT / "scanner" / "models.py",
        ROOT / "scanner" / "engine.py",
        ROOT / "scanner" / "service.py",
    ]

    forbidden = (
        "state.decision",
        "state.trade",
        "state.risk",
        "state.execution",
        "execution_intent",
        "tradeplanner",
        "riskmanager",
        "executiongateway",
        "place_order",
        "submit_order",
        "research.database",
    )

    for path in paths:
        block = path.read_text(encoding="utf-8").lower()

        for term in forbidden:
            assert term not in block, (
                f"{term!r} found in {path}"
            )


def test_scanner_has_no_randomness():
    for path in (
        ROOT / "scanner" / "models.py",
        ROOT / "scanner" / "engine.py",
        ROOT / "scanner" / "service.py",
    ):
        source = path.read_text(encoding="utf-8").lower()
        assert "import random" not in source
        assert "random." not in source


TESTS = [
    value
    for name, value in globals().items()
    if name.startswith("test_")
    and callable(value)
]
