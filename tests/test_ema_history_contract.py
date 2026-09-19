from indicators.ema import ema, ema_value


def _candles(count):
    return [
        {
            "open": 100.0 + i * 0.1,
            "high": 101.0 + i * 0.1,
            "low": 99.0 + i * 0.1,
            "close": 100.0 + i * 0.1,
            "volume": 1000.0,
        }
        for i in range(count)
    ]


def test_ema200_is_unavailable_below_required_history():
    closes = [100.0 + i * 0.1 for i in range(199)]

    assert ema_value(closes, 200) is None


def test_ema200_is_available_at_required_history():
    closes = [100.0 + i * 0.1 for i in range(200)]

    value = ema_value(closes, 200)

    assert value is not None
    assert value > 0


def test_ema_readiness_is_explicit():
    result = ema(_candles(100))

    assert result["ema20"] is not None
    assert result["ema50"] is not None
    assert result["ema100"] is not None
    assert result["ema200"] is None

    assert result["ready"][20] is True
    assert result["ready"][50] is True
    assert result["ready"][100] is True
    assert result["ready"][200] is False

    assert result["trend"] == "UNAVAILABLE"

from core.kernel import JaguarKernel
from indicators.indicator_engine import update_market_state
from engine.ai_brain import analyze as ai_analyze
from engine.market_regime import analyze as regime_analyze
from engine.gann_engine import analyze as gann_analyze


def test_ema_consumers_handle_insufficient_history():
    kernel = JaguarKernel()
    kernel.initialize("TCS.NS", "15m")
    state = kernel.get_state()

    state.market["candles"] = _candles(100)
    update_market_state(state)

    assert state.ema200 is None

    ai = ai_analyze(state)
    regime = regime_analyze(state)
    gann = gann_analyze(state)

    assert "EMA Trend Unavailable" in ai["reasons"]
    assert "EMA Regime Unavailable" in regime["reasons"]
    assert "Gann EMA Angle Unavailable" in gann["reasons"]
