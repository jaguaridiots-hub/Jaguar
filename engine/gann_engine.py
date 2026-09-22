from core.engine_result import EngineResult
import math


def analyze(state):

    price = state.price
    atr = state.atr

    reasons = []
    score = 0

    root = math.sqrt(price)

    support = round((root - 1) ** 2, 2)
    resistance = round((root + 1) ** 2, 2)

    ema20 = state.ema20
    ema50 = state.ema50
    ema100 = state.ema100
    ema200 = state.ema200

    angle = "SIDEWAYS"

    ema_ready = all(
        value is not None
        for value in (ema20, ema50, ema100, ema200)
    )

    if ema_ready:
        if ema20 > ema50 > ema100 > ema200:
            angle = "1x1 BULLISH"
            score += 2
            reasons.append("Bullish Gann Angle")

        elif ema20 < ema50 < ema100 < ema200:
            angle = "1x1 BEARISH"
            score -= 2
            reasons.append("Bearish Gann Angle")
    else:
        reasons.append("Gann EMA Angle Unavailable")

    cycle = "UNKNOWN"

    if ema20 is not None:
        if price > ema20:
            cycle = "UP"
            score += 1
            reasons.append("Up Cycle")
        else:
            cycle = "DOWN"
            score -= 1
            reasons.append("Down Cycle")
    else:
        reasons.append("Gann EMA20 Cycle Unavailable")

    if abs(price - support) < atr:
        score += 1
        reasons.append("Near Gann Support")

    if abs(price - resistance) < atr:
        score -= 1
        reasons.append("Near Gann Resistance")

    if int(price) % 9 == 0:
        score += 1
        reasons.append("9 Cycle")

    elif int(price) % 45 == 0:
        score += 2
        reasons.append("45 Cycle")

    elif int(price) % 90 == 0:
        score += 3
        reasons.append("90 Cycle")

    signal = "NEUTRAL"

    if score >= 3:
        signal = "BULLISH"

    elif score <= -3:
        signal = "BEARISH"

    confidence = min(1.0, abs(score) / 5)

    return EngineResult(
        name="Gann",
        signal=signal,
        score=score,
        confidence=confidence,
        weight=1.20,
        reasons=reasons,
        metadata={
            "support": support,
            "resistance": resistance,
            "angle": angle,
            "cycle": cycle
        }
    ).to_dict()
