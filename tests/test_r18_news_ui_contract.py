"""33C-R18 NEWS UI dependency-free contract tests."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT.joinpath(
    "dashboard",
    "command_center_v3.py",
).read_text(encoding="utf-8")


def test_news_section_exists():
    assert "R18_NEWS_UI_START" in SOURCE
    assert "JAGUAR NEWS" in SOURCE
    assert 'id="newsList"' in SOURCE


def test_news_filters_exist():
    assert 'id="newsSymbolFilter"' in SOURCE
    assert 'id="newsCategoryFilter"' in SOURCE


def test_news_refresh_exists():
    assert 'id="newsRefresh"' in SOURCE
    assert "loadNews(true)" in SOURCE


def test_news_fetches_news_api():
    assert "fetch(" in SOURCE
    assert "`/news?" in SOURCE
    assert 'params.set("limit","20")' in SOURCE


def test_news_renders_required_fields():
    assert "item.publisher" in SOURCE
    assert "item.title" in SOURCE
    assert "item.published_at" in SOURCE
    assert "item.url" in SOURCE
    assert "item.category" in SOURCE


def test_news_supports_current_cached_unavailable():
    assert '"CURRENT"' in SOURCE
    assert '"CACHED"' in SOURCE
    assert '"UNAVAILABLE"' in SOURCE
    assert "cached" in SOURCE


def test_news_empty_state_exists():
    assert "No news items available for this filter." in SOURCE
    assert "News providers unavailable and no cached news is available." in SOURCE


def test_news_links_open_safely():
    assert 'target="_blank"' in SOURCE
    assert 'rel="noopener noreferrer"' in SOURCE


def test_core_dashboard_state_route_remains():
    assert "/dashboard/state?symbol=" in SOURCE


def test_news_ui_has_no_execution_authority_reference():
    start = SOURCE.index("R18_NEWS_UI_START", SOURCE.index("<style>"))
    end = SOURCE.index("R18_NEWS_UI_END", start)

    block = SOURCE[start:end].lower()

    forbidden = (
        "tradeplanner",
        "riskmanager",
        "executionconfirmation",
        "executiongateway",
        "execution_intent",
    )

    for term in forbidden:
        assert term not in block


TESTS = [
    test_news_section_exists,
    test_news_filters_exist,
    test_news_refresh_exists,
    test_news_fetches_news_api,
    test_news_renders_required_fields,
    test_news_supports_current_cached_unavailable,
    test_news_empty_state_exists,
    test_news_links_open_safely,
    test_core_dashboard_state_route_remains,
    test_news_ui_has_no_execution_authority_reference,
]
