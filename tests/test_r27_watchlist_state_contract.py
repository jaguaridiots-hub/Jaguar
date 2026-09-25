from pathlib import Path

SOURCE = Path(
    "dashboard/command_center_v3.py"
).read_text(encoding="utf-8")


START = "/* R27_WATCHLIST_STATE_START */"
END = "/* R27_WATCHLIST_STATE_END */"


def _block():
    start = SOURCE.index(START)
    end = SOURCE.index(END, start)
    return SOURCE[start:end + len(END)]


def test_r27_markers_exist():
    assert SOURCE.count(START) == 1
    assert SOURCE.count(END) == 1


def test_r27_has_dedicated_storage_key():
    block = _block()
    assert "jaguarQuantXActiveWatchSymbol" in block


def test_r27_uses_session_storage():
    block = _block()
    assert "sessionStorage.getItem" in block
    assert "sessionStorage.setItem" in block


def test_r27_validates_watchlist_symbol():
    block = _block()

    assert "R27_VALID_WATCH_SYMBOLS" in block
    assert "BTCUSDT" in block
    assert "RELIANCE.NS" in block


def test_r27_invalid_symbol_falls_back_to_default():
    block = _block()

    assert 'return "BTCUSDT";' in block
    assert "R27_VALID_WATCH_SYMBOLS.has" in block


def test_r27_reads_symbol_before_watch_render():
    assert "const initialSymbol=readR27ActiveWatchSymbol();" in SOURCE

    startup_start = SOURCE.index("const initialSymbol=readR27ActiveWatchSymbol();")
    startup_end = SOURCE.index("initR24DashboardTabs();", startup_start)
    startup = SOURCE[startup_start:startup_end]

    assert "setActiveSymbol(" in startup
    assert "initialSymbol" in startup
    assert "renderWatchlist:true" in startup
    assert "refresh:false" in startup


def test_r27_watch_click_persists_symbol():
    block_start = SOURCE.index("function renderWatch(){")
    block_end = SOURCE.index("function freshnessLabel", block_start)
    block = SOURCE[block_start:block_end]

    assert "setActiveSymbol(" in block
    assert "b.dataset.symbol" in block
    assert "persistWatchlist:true" in block


def test_r27_watch_click_rerenders_watchbar():
    block_start = SOURCE.index("function renderWatch(){")
    block_end = SOURCE.index("function freshnessLabel", block_start)
    block = SOURCE[block_start:block_end]

    assert "setActiveSymbol(" in block
    assert "renderWatchlist:true" in block


def test_r27_watch_click_preserves_existing_load():
    block_start = SOURCE.index("function renderWatch(){")
    block_end = SOURCE.index("function freshnessLabel", block_start)
    block = SOURCE[block_start:block_end]

    assert "setActiveSymbol(" in block
    assert "refresh:true" in block


def test_r27_state_layer_is_local_only():
    block = _block().lower()

    forbidden = (
        "fetch(",
        "xmlhttprequest",
        "/scanner",
        "/news",
        "/dashboard/state",
    )

    for item in forbidden:
        assert item not in block


def test_r27_has_no_trading_authority():
    block = _block().lower()

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


def test_r27_preserves_tab_state():
    assert "R26_TAB_STORAGE_KEY" in SOURCE
    assert "readR26ActiveTab" in SOURCE
    assert "persistR26ActiveTab" in SOURCE


def test_r27_preserves_previous_contracts():
    for marker in (
        "R24_DASHBOARD_TABS_UI_START",
        "R25_DASHBOARD_TABS_HARDENING_START",
        "R26_DASHBOARD_TAB_STATE_START",
    ):
        assert marker in SOURCE


def run_all():
    tests = (
        test_r27_markers_exist,
        test_r27_has_dedicated_storage_key,
        test_r27_uses_session_storage,
        test_r27_validates_watchlist_symbol,
        test_r27_invalid_symbol_falls_back_to_default,
        test_r27_reads_symbol_before_watch_render,
        test_r27_watch_click_persists_symbol,
        test_r27_watch_click_rerenders_watchbar,
        test_r27_watch_click_preserves_existing_load,
        test_r27_state_layer_is_local_only,
        test_r27_has_no_trading_authority,
        test_r27_preserves_tab_state,
        test_r27_preserves_previous_contracts,
    )

    for test in tests:
        test()

    print(
        f"R27_CONTRACT=PASS "
        f"({len(tests)}/{len(tests)})"
    )


if __name__ == "__main__":
    run_all()
