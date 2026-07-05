from indicators.ema import ema20, ema50, ema100, ema200
from indicators.atr import atr


def analyze(state):

    reasons = []

    score = 0

    if ema20 > ema50 > ema100 > ema200:
        regime = "TRENDING BULL"
        score = 3
        reasons.append("EMA Bull Trend")

    elif ema20 < ema50 < ema100 < ema200:
        regime = "TRENDING BEAR"
        score = -3
        reasons.append("EMA Bear Trend")

    else:
        regime = "RANGING"
        reasons.append("EMA Sideways")

    price = state.price if state.price > 0 else ema20
    atr_percent = (atr / price) * 100

    if atr_percent >= 3:
        volatility = "HIGH"

    elif atr_percent >= 1:
        volatility = "NORMAL"

    else:
        volatility = "LOW"

    return {
        "regime": regime,
        "volatility": volatility,
        "score": score,
        "reasons": reasons
    }
