"""33C-R19 Scanner dashboard UI static contracts."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (
    ROOT
    / "dashboard"
    / "command_center_v3.py"
).read_text(encoding="utf-8")


def _r19_blocks():
    blocks = []
    cursor = 0

    while True:
        start = SOURCE.find(
            "R19_SCANNER_UI_START",
            cursor,
        )

        if start < 0:
            break

        end = SOURCE.find(
            "R19_SCANNER_UI_END",
            start,
        )

        assert end >= 0, "unclosed R19 scanner UI block"

        blocks.append(
            SOURCE[start:end]
        )

        cursor = end + len(
            "R19_SCANNER_UI_END"
        )

    assert len(blocks) == 3, (
        f"expected 3 R19 blocks, found {len(blocks)}"
    )

    return blocks


def _all_r19():
    return "\n".join(_r19_blocks())


def test_r19_has_css_html_js_blocks():
    blocks = _r19_blocks()

    assert ".scanner-card" in blocks[0]
    assert 'id="scannerSymbol"' in blocks[1]
    assert "function renderScanner()" in blocks[2]


def test_scanner_panel_exists():
    source = _all_r19()

    assert "JAGUAR SCANNER" in source
    assert "CANDIDATE DISCOVERY" in source


def test_scanner_controls_exist():
    source = _all_r19()

    assert 'id="scannerSymbol"' in source
    assert 'id="scannerScanSymbol"' in source
    assert 'id="scannerScanWatchlist"' in source


def test_scanner_output_containers_exist():
    source = _all_r19()

    assert 'id="scannerStatus"' in source
    assert 'id="scannerError"' in source
    assert 'id="scannerList"' in source


def test_scanner_state_exists():
    assert "scanner:null" in SOURCE


def test_scanner_functions_exist():
    source = _all_r19()

    assert "function renderScanner()" in source
    assert "async function loadScanner(" in source
    assert "function initScannerControls()" in source


def test_scanner_calls_api():
    source = _all_r19()

    assert "/scanner?symbol=" in source
    assert 'encodeURIComponent(activeSymbol)' in source
    assert '"/scanner"' in source


def test_scanner_supports_symbol_and_watchlist():
    source = _all_r19()

    assert "SCAN SYMBOL" in source
    assert "SCAN WATCHLIST" in source
    assert 'loadScanner("")' in source


def test_scanner_renders_candidate_fields():
    source = _all_r19()

    required = (
        "candidate.symbol",
        "candidate.direction",
        "candidate.score",
        "candidate.confidence",
        "candidate.structure",
        "candidate.data_quality",
        "candidate.evidence",
    )

    for term in required:
        assert term in source


def test_scanner_renders_structure_and_mtf():
    source = _all_r19()

    assert "structure.bos" in source
    assert "quality.mtf" in source
    assert "MTF ALIGNMENT" in source


def test_scanner_renders_quality_and_status():
    source = _all_r19()

    assert "DATA QUALITY" in source
    assert "CURRENT" in source
    assert "DEGRADED" in source
    assert "UNAVAILABLE" in source


def test_scanner_has_loading_state():
    source = _all_r19()

    assert "SCANNING…" in source
    assert "button.disabled=true" in source


def test_scanner_has_explicit_candidate_boundary():
    source = _all_r19()

    assert "SCANNER CANDIDATE ONLY" in source
    assert "NOT EXECUTION AUTHORIZATION" in source


def test_scanner_does_not_modify_canonical_dashboard_state():
    source = _all_r19().lower()

    forbidden = (
        "state.ui.idm",
        "state.ui.trade",
        "state.ui.risk",
        "state.ui.execution",
        "state.decision",
        "state.trade",
        "state.risk",
        "state.execution",
    )

    for term in forbidden:
        assert term not in source


def test_scanner_ui_does_not_reference_execution_authority():
    source = _all_r19().lower()

    forbidden = (
        "tradeplanner",
        "riskmanager",
        "executionconfirmation",
        "executiongateway",
        "execution_intent",
        "place_order",
        "submit_order",
        "research.database",
    )

    for term in forbidden:
        assert term not in source


def test_scanner_is_not_in_main_dashboard_refresh():
    start = SOURCE.index("async function load(){")
    end = SOURCE.index(
        'document.getElementById("aiForm")',
        start,
    )

    main_load = SOURCE[start:end]

    assert "loadScanner(" not in main_load


def test_scanner_does_not_auto_scan():
    source = SOURCE

    init_start = source.index(
        "function initScannerControls(){"
    )

    init_end = source.index(
        "/* R19_SCANNER_UI_END */",
        init_start,
    )

    init_block = source[init_start:init_end]

    # Initialization renders the idle scanner state only.
    assert "renderScanner();" in init_block

    # Scanner execution is attached only to explicit button handlers.
    first_click = init_block.index(
        "scanSymbolEl.onclick=()=>{"
    )

    second_click = init_block.index(
        "scanWatchlistEl.onclick=()=>{"
    )

    assert first_click >= 0
    assert second_click >= 0

    symbol_load = init_block.index(
        "loadScanner(symbol);",
        first_click,
    )

    watchlist_load = init_block.index(
        'loadScanner("");',
        second_click,
    )

    assert symbol_load > first_click
    assert watchlist_load > second_click

    # There must be no scanner invocation before the first explicit handler.
    first_load = init_block.find("loadScanner(")

    assert first_load > first_click
    assert first_load != -1
def test_existing_r18_news_ui_remains():
    assert "R18_NEWS_UI_START" in SOURCE
    assert "R18_NEWS_UI_END" in SOURCE
    assert 'id="newsList"' in SOURCE
    assert "async function loadNews(" in SOURCE


def test_dashboard_state_contract_remains():
    assert "/dashboard/state?symbol=" in SOURCE
    assert "state.ui=d.ui" in SOURCE
    assert "state.candles=Array.isArray(d.candles)" in SOURCE


TESTS = [
    value
    for name, value in globals().items()
    if name.startswith("test_")
    and callable(value)
]
