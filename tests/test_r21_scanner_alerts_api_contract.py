"""R21 scanner-alert API contract tests."""

from __future__ import annotations

from pathlib import Path


SOURCE = Path("api.py").read_text(encoding="utf-8")


def test_alert_service_is_imported():
    assert (
        "from scanner.alerts import ScannerAlertService"
        in SOURCE
    )


def test_alert_service_is_constructed():
    assert (
        "scanner_alert_service = ScannerAlertService("
        in SOURCE
    )


def test_alert_route_exists():
    assert (
        '@app.get("/scanner/alerts"'
        in SOURCE
    )


def test_alert_route_exposes_symbol_filter():
    start = SOURCE.index(
        '@app.get("/scanner/alerts"'
    )
    block = SOURCE[start:]

    assert "symbol: str | None = None" in block


def test_alert_route_normalizes_symbol():
    start = SOURCE.index(
        '@app.get("/scanner/alerts"'
    )
    block = SOURCE[start:]

    assert (
        'str(symbol).strip().upper()'
        in block
    )


def test_alert_route_rejects_empty_symbol():
    start = SOURCE.index(
        '@app.get("/scanner/alerts"'
    )
    block = SOURCE[start:]

    assert (
        'detail="symbol must not be empty"'
        in block
    )


def test_alert_route_uses_alert_service():
    start = SOURCE.index(
        '@app.get("/scanner/alerts"'
    )
    block = SOURCE[start:]

    assert (
        "scanner_alert_service.scan_watchlist("
        in block
    )


def test_alert_route_serializes_snapshot():
    start = SOURCE.index(
        '@app.get("/scanner/alerts"'
    )
    block = SOURCE[start:]

    assert "snapshot.to_dict()" in block


def test_alert_route_preserves_watchlist_scan():
    start = SOURCE.index(
        '@app.get("/scanner/alerts"'
    )
    block = SOURCE[start:]

    assert "symbols=symbols" in block


def test_alert_route_has_no_execution_authority():
    start = SOURCE.index(
        '@app.get("/scanner/alerts"'
    )
    block = SOURCE[start:].lower()

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


def test_alert_route_does_not_touch_database():
    start = SOURCE.index(
        '@app.get("/scanner/alerts"'
    )
    block = SOURCE[start:].lower()

    assert "database" not in block


def test_original_scanner_route_remains():
    assert (
        '@app.get("/scanner", include_in_schema=False)'
        in SOURCE
    )


def test_news_route_remains():
    assert '@app.get("/news"' in SOURCE
