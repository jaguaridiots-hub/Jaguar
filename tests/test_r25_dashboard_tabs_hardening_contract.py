from pathlib import Path

SOURCE = Path(
    "dashboard/command_center_v3.py"
).read_text(encoding="utf-8")


def _blocks():
    marker = "R25_DASHBOARD_TABS_HARDENING"
    positions = []
    start = 0

    while True:
        pos = SOURCE.find(marker, start)
        if pos == -1:
            break
        positions.append(pos)
        start = pos + 1

    return positions


def _css_block():
    start = SOURCE.index(
        "/* R25_DASHBOARD_TABS_HARDENING_START */"
    )
    end = SOURCE.index(
        "/* R25_DASHBOARD_TABS_HARDENING_END */",
        start,
    )
    return SOURCE[start:end]


def _html_block():
    start = SOURCE.index(
        "<!-- R25_DASHBOARD_TABS_HARDENING_START -->"
    )
    end = SOURCE.index(
        "<!-- R25_DASHBOARD_TABS_HARDENING_END -->",
        start,
    )
    return SOURCE[start:end]


def _js_block():
    marker = "/* R25_DASHBOARD_TABS_HARDENING_START */"
    end_marker = "/* R25_DASHBOARD_TABS_HARDENING_END */"

    css_start = SOURCE.index(marker)
    js_start = SOURCE.index(marker, css_start + len(marker))

    js_end = SOURCE.index(end_marker, js_start)

    return SOURCE[js_start:js_end + len(end_marker)]

def test_r25_markers_exist():
    assert SOURCE.count(
        "/* R25_DASHBOARD_TABS_HARDENING_START */"
    ) == 2
    assert SOURCE.count(
        "/* R25_DASHBOARD_TABS_HARDENING_END */"
    ) == 2
    assert SOURCE.count(
        "<!-- R25_DASHBOARD_TABS_HARDENING_START -->"
    ) == 1
    assert SOURCE.count(
        "<!-- R25_DASHBOARD_TABS_HARDENING_END -->"
    ) == 1


def test_r25_marker_order_css_html_js():
    css = SOURCE.index(
        "/* R25_DASHBOARD_TABS_HARDENING_START */"
    )
    html = SOURCE.index(
        "<!-- R25_DASHBOARD_TABS_HARDENING_START -->"
    )
    js = SOURCE.index(
        "/* R25_DASHBOARD_TABS_HARDENING_START */",
        css + 1,
    )

    assert css < html < js


def test_r25_tablist_semantics():
    html = _html_block()

    assert 'role="tablist"' in html
    assert 'aria-label="Command Center sections"' in html
    assert html.count('role="tab"') >= 5


def test_r25_required_tabs_remain():
    html = _html_block()

    for tab in (
        "overview",
        "market",
        "scanner",
        "news",
        "system",
    ):
        assert f'data-r24-tab="{tab}"' in html


def test_r25_single_default_active_tab():
    html = _html_block()

    assert html.count('aria-selected="true"') == 1
    assert 'id="r24-tab-overview"' in html


def test_r25_keyboard_navigation():
    js = _js_block()

    for key in (
        "keydown",
        "ArrowRight",
        "ArrowLeft",
        "Home",
        "End",
        ".focus()",
    ):
        assert key in js


def test_r25_keyboard_navigation_is_local():
    js = _js_block()

    forbidden = (
        "fetch(",
        "XMLHttpRequest",
        "/scanner",
        "/news",
        "/dashboard/state",
    )

    lowered = js.lower()

    for item in forbidden:
        assert item.lower() not in lowered


def test_r25_no_trading_authority():
    block = (
        _css_block()
        + _html_block()
        + _js_block()
    ).lower()

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

    for item in forbidden:
        assert item not in block


def test_r25_active_state_remains_single():
    js = _js_block()

    assert "aria-selected" in js
    assert "r24-active" in js
    assert "activate(" in js


def test_r25_visibility_router_remains_local():
    js = _js_block()

    assert "r24-tab-hidden" in js
    assert "r24-routed-content" in js
    assert (
        "classList.toggle" in js
        or "setDashboardClassState(" in js
    )


def test_r25_preserves_r24_contract():
    required = (
        "r24DashboardTabs",
        "r24-tab-overview",
        "r24-tab-market",
        "r24-tab-scanner",
        "r24-tab-news",
        "r24-tab-system",
        "r24-panel-overview",
        "r24-panel-market",
        "r24-panel-scanner",
        "r24-panel-news",
        "r24-panel-system",
    )

    for item in required:
        assert item in SOURCE


def test_r25_preserves_previous_feature_markers():
    required = (
        "R18_NEWS_UI_START",
        "R19_SCANNER_UI_START",
        "R21_SCANNER_ALERT_UI_START",
        "R23_SCANNER_ALERT_CONTEXT_UI_START",
    )

    for marker in required:
        assert marker in SOURCE


def test_r25_has_no_auto_tab_network_behavior():
    js = _js_block()

    forbidden = (
        "loadScanner",
        "loadNews",
        "loadScannerAlertContext",
    )

    for item in forbidden:
        assert item not in js


def run_all():
    tests = (
        test_r25_markers_exist,
        test_r25_marker_order_css_html_js,
        test_r25_tablist_semantics,
        test_r25_required_tabs_remain,
        test_r25_single_default_active_tab,
        test_r25_keyboard_navigation,
        test_r25_keyboard_navigation_is_local,
        test_r25_no_trading_authority,
        test_r25_active_state_remains_single,
        test_r25_visibility_router_remains_local,
        test_r25_preserves_r24_contract,
        test_r25_preserves_previous_feature_markers,
        test_r25_has_no_auto_tab_network_behavior,
    )

    for test in tests:
        test()

    print(
        f"R25_CONTRACT=PASS "
        f"({len(tests)}/{len(tests)})"
    )


if __name__ == "__main__":
    run_all()
