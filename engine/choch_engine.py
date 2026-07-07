from core.engine_result import EngineResult
from data.market_data import candles


def analyze(state):

    if len(candles) < 20:
        return EngineResult(
            name="CHOCH",
            signal="NEUTRAL",
            score=0,
            confidence=0,
            weight=1.15,
            reasons=["Not enough candles"]
        ).to_dict()

    highs = [c["high"] for c in candles[-20:]]
    lows = [c["low"] for c in candles[-20:]]
    closes = [c["close"] for c in candles[-20:]]

    last_close = closes[-1]

    recent_high = max(highs[-10:])
    previous_high = max(highs[:10])

    recent_low = min(lows[-10:])
    previous_low = min(lows[:10])

    score = 0
    signal = "NEUTRAL"
    reasons = []

    if recent_high > previous_high and last_close < recent_low:
        signal = "BEARISH"
        score = -4
        reasons.append("Bearish CHOCH")

    elif recent_low < previous_low and last_close > recent_high:
        signal = "BULLISH"
        score = 4
        reasons.append("Bullish CHOCH")

    confidence = min(1.0, abs(score) / 5)

    return EngineResult(
        name="CHOCH",
        signal=signal,
        score=score,
        confidence=confidence,
        weight=1.15,
        reasons=reasons,
        metadata={
            "recent_high": recent_high,
            "recent_low": recent_low,
            "previous_high": previous_high,
            "previous_low": previous_low,
        }
    ).to_dict()
