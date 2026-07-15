"""
Jaguar Quant X
Indicator Engine

Central indicator calculation engine and
MarketState compatibility bridge.
"""

from indicators.ema import ema
from indicators.rsi import rsi
from indicators.volume import volume
from indicators.fibonacci import fibonacci
from indicators.atr import atr
from indicators.macd import macd
from indicators.adx import adx
from indicators.supertrend import supertrend
from indicators.bollinger import bollinger
from indicators.vwap import vwap


class IndicatorEngine:

    @staticmethod
    def calculate(candles):

        if not candles:
            raise ValueError(
                "IndicatorEngine requires candle data"
            )

        return {
            "ema": ema(candles),
            "rsi": rsi(candles),
            "volume": volume(candles),
            "fibonacci": fibonacci(candles),
            "atr": atr(candles),
            "macd": macd(candles),
            "adx": adx(candles),
            "supertrend": supertrend(candles),
            "bollinger": bollinger(candles),
            "vwap": vwap(candles),
        }


# ==========================================
# Internal Helpers
# ==========================================

def _to_float(value, default=0.0):

    try:
        if value is None:
            return default

        return float(value)

    except (TypeError, ValueError):
        return default


def _first_value(data, keys, default=0.0):

    if not isinstance(data, dict):
        return default

    for key in keys:

        if key in data and data[key] is not None:
            return data[key]

    return default


# ==========================================
# MarketState Compatibility Bridge
# ==========================================

def update_market_state(state, candles=None):

    # ======================================
    # Resolve Candle Data
    # ======================================

    if candles is None:

        market = getattr(state, "market", {}) or {}

        candles = market.get("candles", [])

    if not candles:
        raise ValueError(
            "No candles available for indicator calculation"
        )

    # ======================================
    # Calculate Indicators
    # ======================================

    indicators = IndicatorEngine.calculate(candles)

    # ======================================
    # Store Enterprise Indicator Facts
    # ======================================

    state.indicators = indicators

    # ======================================
    # EMA
    # ======================================

    ema_data = indicators.get("ema", {}) or {}

    state.ema20 = _to_float(
        _first_value(
            ema_data,
            ["ema20", "EMA20", "20"]
        )
    )

    state.ema50 = _to_float(
        _first_value(
            ema_data,
            ["ema50", "EMA50", "50"]
        )
    )

    state.ema100 = _to_float(
        _first_value(
            ema_data,
            ["ema100", "EMA100", "100"]
        )
    )

    state.ema200 = _to_float(
        _first_value(
            ema_data,
            ["ema200", "EMA200", "200"]
        )
    )

    # ======================================
    # RSI
    # ======================================

    rsi_data = indicators.get("rsi", 0.0)

    if isinstance(rsi_data, dict):

        state.rsi = _to_float(
            _first_value(
                rsi_data,
                ["rsi", "RSI", "value"]
            )
        )

    else:

        state.rsi = _to_float(rsi_data)

    # ======================================
    # ATR
    # ======================================

    atr_data = indicators.get("atr", 0.0)

    if isinstance(atr_data, dict):

        state.atr = _to_float(
            _first_value(
                atr_data,
                ["atr", "ATR", "value"]
            )
        )

    else:

        state.atr = _to_float(atr_data)

    # ======================================
    # Volume
    # ======================================

    volume_data = indicators.get("volume", {})

    if isinstance(volume_data, dict):

        volume_value = _first_value(
            volume_data,
            ["current", "volume", "Volume", "value"],
            default=None
        )

        if volume_value is not None:
            state.volume = _to_float(volume_value)

    # ======================================
    # Fibonacci
    # ======================================

    fib_data = indicators.get("fibonacci", {})

    if isinstance(fib_data, dict):
        state.fibonacci = fib_data

    # ======================================
    # Enterprise Market Sync
    # ======================================

    if (
        not hasattr(state, "market")
        or not isinstance(
            state.market,
            dict,
        )
    ):
        state.market = {}

    # Canonical analytical candle authority.
    #
    # Structural specialist engines resolve candles
    # from state.market["candles"] through
    # engine.structure_utils.get_candles().
    #
    # Preserve the exact normalized candle dataset
    # used by the indicator calculation cycle.
    state.market["candles"] = candles

    state.market["ema20"] = state.ema20
    state.market["ema50"] = state.ema50
    state.market["ema100"] = state.ema100
    state.market["ema200"] = state.ema200

    state.market["rsi"] = state.rsi
    state.market["atr"] = state.atr
    state.market["volume"] = state.volume

    # ======================================
    # Return Updated State
    # ======================================

    return state
