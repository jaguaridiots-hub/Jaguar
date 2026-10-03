"""33C-R19 scanner API static contract tests.

Dependency-free because the local Termux environment does not have FastAPI.
"""

from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
API = ROOT / "api.py"


def _api_source() -> str:
    return API.read_text(encoding="utf-8")


def _function_source(name: str) -> str:
    source = _api_source()
    tree = ast.parse(source)

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name == name:
                segment = ast.get_source_segment(source, node)
                assert segment is not None
                return segment

    raise AssertionError(f"{name!r} not found")


def test_scanner_service_is_imported():
    source = _api_source()

    assert (
        "from scanner.service import ScannerService"
        in source
    )


def test_scanner_service_is_constructed():
    source = _api_source()

    assert "scanner_service = ScannerService()" in source


def test_scanner_route_exists():
    source = _api_source()

    assert '"/scanner"' in source
    assert "async def scanner(" in source


def test_scanner_route_exposes_symbol_filter():
    source = _function_source("scanner")

    assert "symbol: str | None = None" in source


def test_scanner_route_normalizes_symbol():
    source = _function_source("scanner")

    assert "str(symbol).strip().upper()" in source


def test_scanner_route_rejects_empty_symbol():
    source = _function_source("scanner")

    assert "if not normalized_symbol" in source
    assert "status_code=400" in source


def test_scanner_route_uses_scanner_service():
    source = _function_source("scanner")

    assert "scanner_service.scan_watchlist(" in source
    assert "snapshot.to_dict()" in source


def test_scanner_route_preserves_watchlist_scan():
    source = _function_source("scanner")

    assert "symbols = None" in source
    assert "symbols=symbols" in source


def test_scanner_route_does_not_reference_execution_authority():
    source = _function_source("scanner").lower()

    forbidden = (
        "idm",
        "tradeplanner",
        "riskmanager",
        "executionconfirmation",
        "executiongateway",
        "execution_intent",
        "state.decision",
        "state.trade",
        "state.risk",
        "state.execution",
    )

    for term in forbidden:
        assert term not in source


def test_scanner_route_does_not_touch_database():
    source = _function_source("scanner").lower()

    forbidden = (
        "research.database",
        "sqlite",
        "insert_",
        "update_",
        "delete_",
        "commit(",
    )

    for term in forbidden:
        assert term not in source


def test_existing_core_routes_remain_present():
    source = _api_source()

    assert '"/analyze"' in source
    assert '"/assistant/chat"' in source
    assert '"/news"' in source
    assert '"/dashboard/state"' in source
    assert '"/health"' in source


TESTS = [
    value
    for name, value in globals().items()
    if name.startswith("test_")
    and callable(value)
]
