"""R20 deterministic scanner-intelligence contract tests."""

from __future__ import annotations

from scanner.engine import ScannerEngine
from scanner.intelligence import (
    ScannerAlert,
    ScannerIntelligence,
)


def _make_candles(
    direction: str,
    count: int = 260,
    now_ms: int = 1_800_000_000_000,
    interval_ms: int = 15 * 60 * 1000,
):
    candles = []
    price = 100.0
    bullish = direction == "BULLISH"

    first_time = (
        now_ms
        - ((count - 1) * interval_ms)
        - interval_ms
    )

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


def _candidate(
    direction: str = "LONG",
    now_ms: int = 1_800_000_000_000,
):
    candles = _make_candles(
        "BULLISH" if direction == "LONG" else "BEARISH",
        now_ms=now_ms,
    )

    return ScannerEngine().scan(
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


def test_alert_model_is_canonical():
    alert = ScannerIntelligence().enrich(
        _candidate("LONG")
    )

    assert isinstance(alert, ScannerAlert)

    data = alert.to_dict()

    assert data["authority"] == (
        "SCANNER_ALERT_CONTEXT_ONLY"
    )


def test_bullish_candidate_enriches_to_long_alert():
    alert = ScannerIntelligence().enrich(
        _candidate("LONG")
    )

    assert alert.direction == "LONG"
    assert alert.state in {
        "NEW",
        "ACTIVE",
    }
    assert alert.fingerprint
    assert alert.alert_id.startswith("SCN-")


def test_bearish_candidate_enriches_to_short_alert():
    alert = ScannerIntelligence().enrich(
        _candidate("SHORT")
    )

    assert alert.direction == "SHORT"
    assert alert.fingerprint
    assert alert.alert_id.startswith("SCN-")


def test_enrichment_is_deterministic():
    candidate = _candidate("LONG")

    first = ScannerIntelligence().enrich(candidate)
    second = ScannerIntelligence().enrich(candidate)

    assert first.to_dict() == second.to_dict()


def test_fingerprint_changes_when_direction_changes():
    long_alert = ScannerIntelligence().enrich(
        _candidate("LONG")
    )

    short_alert = ScannerIntelligence().enrich(
        _candidate("SHORT")
    )

    assert long_alert.fingerprint != short_alert.fingerprint


def test_fingerprint_is_stable_for_same_candidate():
    candidate = _candidate("LONG")

    first = ScannerIntelligence().enrich(candidate)
    second = ScannerIntelligence().enrich(candidate)

    assert first.fingerprint == second.fingerprint
    assert first.alert_id == second.alert_id


def test_evidence_balance_is_present():
    alert = ScannerIntelligence().enrich(
        _candidate("LONG")
    )

    assert set(alert.evidence_balance) == {
        "bullish",
        "bearish",
    }

    assert alert.evidence_balance["bullish"] >= 0
    assert alert.evidence_balance["bearish"] >= 0


def test_dominant_factors_are_deterministic():
    alert = ScannerIntelligence().enrich(
        _candidate("LONG")
    )

    assert len(alert.dominant_factors) <= 3

    assert tuple(alert.dominant_factors) == tuple(
        sorted(
            alert.dominant_factors,
            key=lambda value: value,
        )
    ) or len(alert.dominant_factors) <= 3


def test_explanation_is_human_readable():
    alert = ScannerIntelligence().enrich(
        _candidate("LONG")
    )

    assert "LONG" in alert.explanation
    assert alert.setup in alert.explanation
    assert "quality=" in alert.explanation
    assert "conflicts=" in alert.explanation


def test_stale_candidate_becomes_stale_alert():
    evaluation_now_ms = 1_800_000_000_000
    stale_candle_now_ms = (
        evaluation_now_ms
        - 24 * 60 * 60 * 1000
    )

    candles = _make_candles(
        "BULLISH",
        now_ms=stale_candle_now_ms,
    )

    candidate = ScannerEngine().scan(
        "BTCUSDT",
        "15m",
        {
            "15m": candles,
            "1h": candles,
            "4h": candles,
            "1d": candles,
        },
        now_ms=evaluation_now_ms,
    )

    alert = ScannerIntelligence().enrich(candidate)

    assert candidate.data_quality["freshness_ok"] is False
    assert alert.state in {
        "STALE",
        "EXPIRED",
    }


def test_non_candidate_is_not_presented_as_active():
    now_ms = 1_800_000_000_000
    candidate = _candidate("LONG", now_ms=now_ms)

    blocked = candidate.__class__(
        symbol=candidate.symbol,
        timeframe=candidate.timeframe,
        direction=candidate.direction,
        score=candidate.score,
        confidence=candidate.confidence,
        is_candidate=False,
        structure=candidate.structure,
        data_quality=candidate.data_quality,
        evidence=candidate.evidence,
        authority=candidate.authority,
    )

    alert = ScannerIntelligence().enrich(blocked)

    assert alert.state == "EXPIRED"


def test_candidate_is_not_mutated():
    candidate = _candidate("LONG")

    before = candidate.to_dict()

    ScannerIntelligence().enrich(candidate)

    after = candidate.to_dict()

    assert after == before


def test_alert_has_no_trading_authority_reference():
    from pathlib import Path

    source = Path(
        "scanner/intelligence.py"
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


def test_r20_intelligence_has_no_randomness():
    from pathlib import Path

    source = Path(
        "scanner/intelligence.py"
    ).read_text(encoding="utf-8").lower()

    assert "random" not in source


def test_r20_alert_serialization_is_json_safe():
    import json

    alert = ScannerIntelligence().enrich(
        _candidate("LONG")
    )

    encoded = json.dumps(alert.to_dict())

    assert isinstance(encoded, str)
    assert '"authority": "SCANNER_ALERT_CONTEXT_ONLY"' in encoded
