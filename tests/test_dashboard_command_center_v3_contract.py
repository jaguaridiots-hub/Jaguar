from pathlib import Path


def test_command_center_v3_is_read_only():
    source = Path("dashboard/command_center_v3.py").read_text().lower()

    assert "fetch(u" in source
    assert "/dashboard/state" in source
    assert "/assistant/chat" in source

    forbidden = (
        '"/order"',
        "'/order'",
        "place_order",
        "cancel_order",
        "enable_live",
        "execute_trade",
    )

    for token in forbidden:
        assert token not in source


def test_command_center_v3_contains_core_sections():
    source = Path("dashboard/command_center_v3.py").read_text().lower()

    for label in (
        "institutional decision",
        "price structure",
        "structure",
        "risk",
        "execution chain",
        "multi-timeframe market context",
        "why jaguar decided this",
        "portfolio / broker",
        "audit",
        "jaguar ai",
        "no live authority",
    ):
        assert label in source


def test_command_center_v3_contains_indicator_session_market_coverage():
    source = Path("dashboard/command_center_v3.py").read_text()

    for token in (
        "function emaSeries(",
        "function vwapSeries(",
        'id="indicatorToolbar"',
        'id="sessionPanel"',
        'id="marketCoverage"',
        "EMA20",
        "EMA50",
        "EMA100",
        "EMA200",
        "VWAP",
        "CRYPTO",
        "NSE",
        "MCX",
        "US",
    ):
        assert token in source


def test_dashboard_api_exposes_session_and_extended_candles():
    source = Path("api.py").read_text()

    assert 'ui["session"] = {' in source
    assert "for candle in candles[-300:]" in source


def test_v3_load_is_async_and_uses_canonical_dashboard_state_contract():
    source = Path("dashboard/command_center_v3.py").read_text(encoding="utf-8")

    assert source.count("async function load(){") == 1
    assert source.count("\nfunction load(){") == 0
    assert "&mode=${encodeURIComponent(state.mode)}" not in source

    p_session = source.index("function renderSession(){")
    p_markets = source.index("function renderMarkets(){")
    p_controls = source.index("function initIndicatorControls(){")
    p_load = source.index("async function load(){")

    assert p_session < p_load
    assert p_markets < p_load
    assert p_controls < p_load

    load_tail = source[p_load:source.index(
        'document.getElementById("aiForm").addEventListener',
        p_load,
    )]

    assert "function renderSession(){" not in load_tail
    assert "function renderMarkets(){" not in load_tail
    assert "function initIndicatorControls(){" not in load_tail


def test_v3_direction_markup_uses_unescaped_row_markup():
    source = Path("dashboard/command_center_v3.py").read_text(encoding="utf-8")

    assert "function rowMarkup(label,markup)" in source
    assert 'rowMarkup("Direction",directionMarkup(idm.direction))' in source
    assert 'rowMarkup("Direction",directionMarkup(st.direction))' in source
    assert 'rowMarkup("Zone Direction",directionMarkup(st.zone_direction))' in source
    assert '${rowMarkup("Trend",directionMarkup(a.trend))}' in source
