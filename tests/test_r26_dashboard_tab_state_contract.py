from pathlib import Path

SOURCE = Path(
    "dashboard/command_center_v3.py"
).read_text(encoding="utf-8")


JS_START = "/* R26_DASHBOARD_TAB_STATE_START */"
JS_END = "/* R26_DASHBOARD_TAB_STATE_END */"


def _js_block():
    start = SOURCE.index(JS_START)
    end = SOURCE.index(JS_END, start)
    return SOURCE[start:end + len(JS_END)]


def test_r26_state_markers_exist():
    assert SOURCE.count(JS_START) == 1
    assert SOURCE.count(JS_END) == 1


def test_r26_persistent_state_uses_session_storage():
    block = _js_block()

    assert "sessionStorage.getItem" in block
    assert "sessionStorage.setItem" in block


def test_r26_has_dedicated_storage_key():
    block = _js_block()

    assert "jaguarQuantXActiveDashboardTab" in block


def test_r26_valid_tab_names_are_constrained():
    block = _js_block()

    for name in (
        "overview",
        "market",
        "scanner",
        "news",
        "system",
    ):
        assert name in block


def test_r26_invalid_state_falls_back_to_overview():
    block = _js_block()

    assert "overview" in block
    assert 'return "overview";' in block
    assert "R26_VALID_TABS.has" in block


def test_r26_state_is_written_only_after_local_activation():
    assert (
        "button.onclick" in SOURCE
        or 'setDashboardEventHandler(button,"onclick",' in SOURCE
    )
    assert "persistR26ActiveTab(name)" in SOURCE
    assert "if(persist)" in SOURCE
    assert "sessionStorage.setItem" in _js_block()


def test_r26_state_restore_is_local_only():
    block = _js_block().lower()

    forbidden = (
        "fetch(",
        "xmlhttprequest",
        "/scanner",
        "/news",
        "/dashboard/state",
    )

    for item in forbidden:
        assert item not in block


def test_r26_has_no_trading_authority():
    block = _js_block().lower()

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


def test_r26_does_not_modify_api_or_database():
    assert "/scanner" not in SOURCE[
        SOURCE.index(JS_START):
        SOURCE.index(JS_END)
    ]


def test_r26_preserves_r24_tabs():
    for item in (
        "r24-tab-overview",
        "r24-tab-market",
        "r24-tab-scanner",
        "r24-tab-news",
        "r24-tab-system",
    ):
        assert item in SOURCE


def test_r26_preserves_r25_keyboard_behavior():
    for item in (
        "ArrowRight",
        "ArrowLeft",
        "Home",
        "End",
        "keydown",
    ):
        assert item in SOURCE


def test_r26_does_not_create_a_second_tab_authority():
    block = _js_block()

    assert "function activate(" not in block
    assert "function initR24DashboardTabs(" not in block


def run_all():
    tests = (
        test_r26_state_markers_exist,
        test_r26_persistent_state_uses_session_storage,
        test_r26_has_dedicated_storage_key,
        test_r26_valid_tab_names_are_constrained,
        test_r26_invalid_state_falls_back_to_overview,
        test_r26_state_is_written_only_after_local_activation,
        test_r26_state_restore_is_local_only,
        test_r26_has_no_trading_authority,
        test_r26_does_not_modify_api_or_database,
        test_r26_preserves_r24_tabs,
        test_r26_preserves_r25_keyboard_behavior,
        test_r26_does_not_create_a_second_tab_authority,
    )

    for test in tests:
        test()

    print(
        f"R26_CONTRACT=PASS "
        f"({len(tests)}/{len(tests)})"
    )


if __name__ == "__main__":
    run_all()
