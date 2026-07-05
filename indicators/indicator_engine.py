from indicators.ema import ema20, ema50, ema100, ema200
from indicators.rsi import rsi
from indicators.atr import atr
from indicators.volume import signal as volume_signal

from data.market_data import candles


def update_market_state(state):
    state.ema20 = ema20
    state.ema50 = ema50
    state.ema100 = ema100
    state.ema200 = ema200

    state.rsi = rsi
    state.atr = atr

    state.volume = candles[-1]["volume"]

    return volume_signal
