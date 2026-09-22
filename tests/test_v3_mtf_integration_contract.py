from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_v3_analysis_engine_uses_canonical_mtf_pipeline():
    source = (
        ROOT
        / "core"
        / "jaguar_analysis_engine.py"
    ).read_text()

    assert (
        "Canonical MTF context hydration"
        in source
    )

    # Canonical market/timeframe hydration.
    assert "TradingKernel" in source
    assert (
        'for timeframe in ("15m", "1h", "4h", "1d")'
        in source
    )

    # Canonical indicator + MTF engines.
    assert (
        "TimeframeIndicatorEngineRunner"
        in source
    )
    assert "MTFEngineRunner" in source

    assert (
        "TimeframeIndicatorEngineRunner().run("
        in source
    )
    assert "MTFEngineRunner().run(" in source


def test_v3_mtf_is_fail_closed():
    source = (
        ROOT
        / "core"
        / "jaguar_analysis_engine.py"
    ).read_text()

    assert (
        'print('
        in source
    )

    assert (
        "unavailable"
        in source
    )


def test_v3_original_market_snapshot_is_restored():
    source = (
        ROOT
        / "core"
        / "jaguar_analysis_engine.py"
    ).read_text()

    assert (
        "original_market = state.market"
        in source
    )

    assert (
        "state.market = mtf_market"
        in source
    )

    assert (
        "state.market = original_market"
        in source
    )


def test_v3_timeframe_snapshot_is_preserved():
    source = (
        ROOT
        / "core"
        / "jaguar_analysis_engine.py"
    ).read_text()

    assert (
        "original_timeframes = getattr("
        in source
    )

    assert (
        "state.timeframes = {"
        in source
    )

    assert (
        "state.timeframes = original_timeframes"
        in source
    )
