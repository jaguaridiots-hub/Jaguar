from indicators.ema import ema20, ema50, ema100, ema200
from indicators.rsi import rsi
from indicators.volume import signal as volume_signal


def analyze(state):
    score = 0
    reasons = []

    # =============================
    # EMA TREND
    # =============================

    if ema20 > ema50 > ema100 > ema200:
        score += 3
        reasons.append("EMA Bullish")

    elif ema20 < ema50 < ema100 < ema200:
        score -= 3
        reasons.append("EMA Bearish")

    # =============================
    # RSI
    # =============================

    if rsi < 30:
        score += 2
        reasons.append("RSI Oversold")

    elif rsi > 70:
        score -= 2
        reasons.append("RSI Overbought")

    # =============================
    # VOLUME
    # =============================

    if volume_signal == "HIGH VOLUME":
        score += 2
        reasons.append("High Volume")

    else:
        score -= 1
        reasons.append("Low Volume")

    # =============================
    # PROBABILITY
    # =============================

    probability = min(95, max(5, 50 + score * 8))

    # =============================
    # DECISION
    # =============================

    if score >= 6:
        decision = "🟢 STRONG BUY"

    elif score >= 3:
        decision = "🟢 BUY"

    elif score >= 1:
        decision = "🟡 WAIT"

    elif score <= -6:
        decision = "🔴 STRONG SELL"

    elif score <= -3:
        decision = "🔴 SELL"

    else:
        decision = "⚪ NEUTRAL"

    return {
        "score": score,
        "probability": probability,
        "decision": decision,
        "reasons": reasons
    }
