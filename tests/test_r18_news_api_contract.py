"""33C-R18 /news API static contract.

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


def test_news_service_is_imported():
    source = _api_source()
    assert "from news.service import JaguarNewsService" in source


def test_news_service_is_constructed():
    source = _api_source()
    assert "news_service = JaguarNewsService()" in source


def test_news_route_exists():
    source = _api_source()
    assert '"/news"' in source
    assert "async def news(" in source


def test_news_route_exposes_required_filters():
    source = _function_source("news")

    assert "symbol: str | None = None" in source
    assert 'category: str = "MARKET"' in source
    assert "limit: int = 20" in source
    assert "refresh: bool = False" in source


def test_news_route_validates_limit():
    source = _function_source("news")

    assert "if limit < 1 or limit > 50" in source
    assert 'status_code=400' in source


def test_news_route_uses_news_service():
    source = _function_source("news")

    assert "news_service.get_news(" in source
    assert "snapshot.to_dict()" in source


def test_news_route_does_not_reference_execution_authority():
    source = _function_source("news").lower()

    forbidden = (
        "idm",
        "tradeplanner",
        "riskmanager",
        "executionconfirmation",
        "executiongateway",
        "execution_intent",
    )

    for term in forbidden:
        assert term not in source


def test_news_route_does_not_touch_database():
    source = _function_source("news").lower()

    forbidden = (
        "research.database",
        "sqlite3",
        "insert_",
        "update_",
        "delete_",
        "create table",
        "alter table",
    )

    for term in forbidden:
        assert term not in source


def test_existing_core_routes_remain_present():
    source = _api_source()

    assert '@app.post("/analyze")' in source
    assert '@app.get("/dashboard/state"' in source


TESTS = [
    test_news_service_is_imported,
    test_news_service_is_constructed,
    test_news_route_exists,
    test_news_route_exposes_required_filters,
    test_news_route_validates_limit,
    test_news_route_uses_news_service,
    test_news_route_does_not_reference_execution_authority,
    test_news_route_does_not_touch_database,
    test_existing_core_routes_remain_present,
]
