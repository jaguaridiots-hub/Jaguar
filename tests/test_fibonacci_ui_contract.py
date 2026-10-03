from types import SimpleNamespace

from dashboard.ui_state import build_ui_state
from dashboard.command_center_v3 import render_command_center_v3


def _state():
    fib = {
        "name": "Fibonacci",
        "signal": "NEUTRAL",
        "score": 3,
        "confidence": 0.75,
        "reasons": ["MID_RANGE", "PREMIUM"],
        "metadata": {
            "lookback": 100,
            "candle_count": 300,
            "price": 81596.0,
            "swing_high": 82100.0,
            "swing_low": 80165.49,
            "range": 1934.51,
            "status": "MID_RANGE",
            "zone": "PREMIUM",
            "retracements": {
                "0.0": 82100.0,
                "23.6": 81643.46,
                "38.2": 81361.02,
                "50.0": 81132.74,
                "61.8": 80904.47,
                "78.6": 80579.48,
                "100.0": 80165.49,
            },
            "extensions": {
                "127.2": 82626.19,
                "161.8": 83295.53,
                "261.8": 85230.04,
            },
        },
    }

    return SimpleNamespace(
        symbol="BTCUSDT",
        timeframe="15m",
        interval="15m",
        fibonacci=fib,
        market={
            "15m": {
                "candles": [
                    {
                        "close": 81596.0,
                        "time": 1,
                    }
                ]
            }
        },
        market_metadata={"freshness": "CURRENT"},
        mtf_indicators={},
        idm={},
        structure={},
        structural_zone={},
        risk={},
        execution={},
        run_id="TEST",
    )


def test_ui_state_exposes_grouped_canonical_fibonacci_levels():
    ui = build_ui_state(_state())

    fib = ui["fibonacci"]
    metadata = fib["metadata"]

    assert fib["status"] == "MID_RANGE"
    assert fib["zone"] == "PREMIUM"
    assert fib["signal"] == "NEUTRAL"

    assert metadata["retracements"]["23.6"] == 81643.46
    assert metadata["retracements"]["38.2"] == 81361.02

    assert metadata["extensions"]["127.2"] == 82626.19
    assert metadata["extensions"]["161.8"] == 83295.53
    assert metadata["extensions"]["261.8"] == 85230.04

    assert "261.8" not in metadata["retracements"]


def test_command_center_has_canonical_fibonacci_presentation_contract():
    html = render_command_center_v3()

    assert 'id="fibonacciPanel"' in html
    assert 'data-indicator="FIB_RETR"' in html
    assert 'data-indicator="FIB_EXT"' in html
    assert "function renderFibonacci()" in html
    assert "state.ui?.fibonacci?.metadata" in html
    assert "fibMetadata.retracements" in html
    assert "fibMetadata.extensions" in html
    assert "No canonical levels available." in html
