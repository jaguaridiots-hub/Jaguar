"""Offline dashboard -> Assistant V2 contract tests."""

from pathlib import Path
import ast


def _source(path):
    return Path(path).read_text(encoding="utf-8")


def test_dashboard_posts_to_assistant_endpoint_without_context():
    source = _source("dashboard/generate.py")

    assert "fetch('/assistant/chat'" in source
    assert "localhost:8082/chat" not in source
    assert "context: state" not in source
    assert "symbol: state.symbol" in source
    assert "interval: state.interval || '15m'" in source
    assert "mode: state.mode || 'SWING'" in source


def test_dashboard_embeds_analysis_interval():
    source = _source("dashboard/generate.py")
    assert '"interval": interval,' in source


def test_api_has_restricted_dashboard_routes():
    source = _source("api.py")
    tree = ast.parse(source)

    route_paths = set()

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for decorator in node.decorator_list:
                if not isinstance(decorator, ast.Call):
                    continue
                if not isinstance(decorator.func, ast.Attribute):
                    continue
                if decorator.func.attr != "get":
                    continue
                if decorator.args and isinstance(decorator.args[0], ast.Constant):
                    route_paths.add(decorator.args[0].value)

    assert "/dashboard" in route_paths
    assert "/dashboard/" in route_paths
    assert "/dashboard/{filename:path}" in route_paths
    assert "_DASHBOARD_FIXED_FILES" in source
    assert 'candidate.name.startswith("dashboard_")' in source
    assert "candidate.parent != DASHBOARD_ROOT" in source


def test_assistant_endpoint_remains_present():
    source = _source("api.py")
    assert '@app.post("/assistant/chat")' in source
