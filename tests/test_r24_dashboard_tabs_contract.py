from pathlib import Path

SOURCE = Path("dashboard/command_center_v3.py").read_text(encoding="utf-8")


def _block(start_marker: str, end_marker: str) -> str:
    start = SOURCE.index(start_marker)
    end = SOURCE.index(end_marker, start)
    return SOURCE[start:end + len(end_marker)]


def test_r24_markers_exist():
    markers = (
        "R24_DASHBOARD_TABS_UI_START",
        "R24_DASHBOARD_TABS_UI_END",
    )
    for marker in markers:
        assert marker in SOURCE


def test_r24_css_html_js_order():
    css_start = SOURCE.index(
        "/* R24_DASHBOARD_TABS_UI_START */"
    )
    html_start = SOURCE.index(
        "<!-- R24_DASHBOARD_TABS_UI_START -->"
    )
    js_start = SOURCE.index(
        "/* R24_DASHBOARD_TABS_UI_START */",
        css_start + 1,
    )

    assert css_start < html_start < js_start


def test_r24_required_tabs():
    block = SOURCE
    required = (
        "r24-tab-overview",
        "r24-tab-market",
        "r24-tab-scanner",
        "r24-tab-news",
        "r24-tab-system",
    )
    for item in required:
        assert item in block


def test_r24_required_panel_ids():
    required = (
        "r24-panel-overview",
        "r24-panel-market",
        "r24-panel-scanner",
        "r24-panel-news",
        "r24-panel-system",
    )
    for item in required:
        assert item in SOURCE


def test_r24_tabs_are_local_ui_only():
    block = _block(
        "/* R24_DASHBOARD_TABS_UI_START */",
        "/* R24_DASHBOARD_TABS_UI_END */",
    ) + _block(
        "<!-- R24_DASHBOARD_TABS_UI_START -->",
        "<!-- R24_DASHBOARD_TABS_UI_END -->",
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

    lowered = block.lower()
    for item in forbidden:
        assert item not in lowered


def test_r24_does_not_remove_previous_ui_markers():
    required = (
        "R18_NEWS_UI_START",
        "R18_NEWS_UI_END",
        "R19_SCANNER_UI_START",
        "R19_SCANNER_UI_END",
        "R21_SCANNER_ALERT_UI_START",
        "R21_SCANNER_ALERT_UI_END",
        "R23_SCANNER_ALERT_CONTEXT_UI_START",
        "R23_SCANNER_ALERT_CONTEXT_UI_END",
    )
    for marker in required:
        assert marker in SOURCE


def test_r24_has_single_active_tab_contract():
    required = (
        "r24-active",
        "aria-selected",
        "r24-panel",
    )
    for item in required:
        assert item in SOURCE


def test_r24_routed_content_uses_dedicated_route_attribute():
    assert (
        'el.dataset.r24Route=group.name' in SOURCE
        or 'setDashboardDatasetValue(el,"r24Route",group.name);' in SOURCE
    )
    assert 'querySelectorAll(".r24-routed-content")' in SOURCE
    assert 'el.dataset.r24Route!==name' in SOURCE


def test_r24_does_not_route_tab_buttons_as_content():
    assert 'querySelectorAll("[data-r24-tab]")' not in SOURCE


def test_r24_panels_do_not_create_layout_space():
    css = _block(
        "/* R24_DASHBOARD_TABS_UI_START */",
        "/* R24_DASHBOARD_TABS_UI_END */",
    )
    assert "display:none !important" in css


def test_r24_scanner_group_contains_r19_r21_r23():
    for selector in (
        '".scanner-card"',
        '".scanner-alert-card"',
        '".scanner-alert-context-card"',
    ):
        assert selector in SOURCE


def test_r24_news_group_contains_r18_news():
    assert '".news-card"' in SOURCE


def test_r24_tabs_do_not_make_network_calls():
    block = _block(
        "/* R24_DASHBOARD_TABS_UI_START */",
        "/* R24_DASHBOARD_TABS_UI_END */",
    )
    forbidden = (
        "fetch(",
        "XMLHttpRequest",
        "/scanner",
        "/news",
        "/dashboard/state",
    )
    for item in forbidden:
        assert item not in block


def test_r24_default_tab_is_overview():
    block = _block(
        "<!-- R24_DASHBOARD_TABS_UI_START -->",
        "<!-- R24_DASHBOARD_TABS_UI_END -->",
    )
    assert "r24-tab-overview" in block
    assert "r24-panel-overview" in block


def run_all():
    tests = (
        test_r24_markers_exist,
        test_r24_css_html_js_order,
        test_r24_required_tabs,
        test_r24_required_panel_ids,
        test_r24_tabs_are_local_ui_only,
        test_r24_does_not_remove_previous_ui_markers,
        test_r24_has_single_active_tab_contract,
        test_r24_default_tab_is_overview,
        test_r24_routed_content_uses_dedicated_route_attribute,
        test_r24_does_not_route_tab_buttons_as_content,
        test_r24_panels_do_not_create_layout_space,
        test_r24_scanner_group_contains_r19_r21_r23,
        test_r24_news_group_contains_r18_news,
        test_r24_tabs_do_not_make_network_calls,
    )

    for test in tests:
        test()

    print(f"R24_CONTRACT=PASS ({len(tests)}/{len(tests)})")


if __name__ == "__main__":
    run_all()
