"""R21 scanner-alert dashboard contract tests."""

from pathlib import Path


SOURCE = Path(
    "dashboard/command_center_v3.py"
).read_text(encoding="utf-8")


def _blocks():
    result=[]
    cursor=0

    while True:
        start=SOURCE.find(
            "R21_SCANNER_ALERT_UI_START",
            cursor,
        )

        if start < 0:
            break

        end=SOURCE.find(
            "R21_SCANNER_ALERT_UI_END",
            start,
        )

        assert end >= 0

        result.append(
            SOURCE[start:end]
        )

        cursor=end+len(
            "R21_SCANNER_ALERT_UI_END"
        )

    return result


def test_r21_has_css_html_js_blocks():
    blocks=_blocks()

    assert len(blocks)==3
    assert ".scanner-alert-card" in blocks[0]
    assert "<details" in blocks[1]
    assert "function loadScannerAlerts" in blocks[2]


def test_alert_panel_exists():
    assert (
        'class="card scanner-alert-card"'
        in SOURCE
    )


def test_alert_controls_exist():
    assert "scannerAlertSymbol" in SOURCE
    assert "scannerAlertScanSymbol" in SOURCE
    assert "scannerAlertScanWatchlist" in SOURCE


def test_alert_output_exists():
    assert "scannerAlertStatus" in SOURCE
    assert "scannerAlertList" in SOURCE


def test_alert_state_is_local():
    blocks="\n".join(_blocks())

    assert "let r21ScannerAlerts = null;" in blocks
    assert "state.decision" not in blocks
    assert "state.trade" not in blocks
    assert "state.risk" not in blocks
    assert "state.execution" not in blocks


def test_alert_calls_api():
    blocks="\n".join(_blocks())

    assert "/scanner/alerts" in blocks
    assert "fetch(" in blocks


def test_alert_supports_symbol_and_watchlist():
    blocks="\n".join(_blocks())

    assert "loadScannerAlerts(symbol)" in blocks
    assert 'loadScannerAlerts("")' in blocks


def test_alert_renders_required_fields():
    blocks="\n".join(_blocks())

    for term in (
        "alert.symbol",
        "alert.direction",
        "alert.setup",
        "alert.priority",
        "alert.state",
        "alert.confidence",
        "alert.explanation",
    ):
        assert term in blocks


def test_alert_renders_factors_and_confluence():
    blocks="\n".join(_blocks())

    assert "dominant_factors" in blocks
    assert "confluence_score" in blocks
    assert "conflict_count" in blocks


def test_alert_has_loading_state():
    blocks="\n".join(_blocks())

    assert "SCANNING…" in blocks
    assert "disabled=true" in blocks


def test_alert_does_not_auto_scan():
    blocks="\n".join(_blocks())

    init_start=blocks.index(
        "function initScannerAlertControls"
    )

    init_block=blocks[init_start:]

    assert "renderScannerAlerts();" in init_block
    assert "loadScannerAlerts(" not in (
        init_block[
            :init_block.index(
                "function initScannerAlertControls"
            )
            + 100
        ]
    )


def test_alert_ui_has_explicit_context_boundary():
    blocks="\n".join(_blocks())

    assert (
        "CONTEXTUAL ALERTS"
        in blocks
    )


def test_alert_ui_has_no_execution_authority():
    blocks="\n".join(_blocks()).lower()

    forbidden=(
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

    for term in forbidden:
        assert term not in blocks, term


def test_r19_scanner_ui_remains():
    assert "R19_SCANNER_UI_START" in SOURCE
    assert "R19_SCANNER_UI_END" in SOURCE


def test_r18_news_ui_remains():
    assert "R18_NEWS_UI_START" in SOURCE
    assert "R18_NEWS_UI_END" in SOURCE


def test_r18_news_api_remains():
    api = Path("api.py").read_text(encoding="utf-8")

    assert '@app.get("/news"' in api
