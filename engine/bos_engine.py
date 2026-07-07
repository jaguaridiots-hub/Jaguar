from core.engine_result import EngineResult
from data.market_data import candles


def analyze(state):

    if len(candles) < 10:
        return EngineResult(
            name="BOS",
            signal="NEUTRAL",
            score=0,
            confidence=0,
            weight=1.15,
            reasons=["Not enough candles"]
        ).to_dict()

    highs = [c["high"] for c in candles[-10:]]
    lows = [c["low"] for c in candles[-10:]]

    last_close = candles[-1]["close"]

    previous_high = max(highs[:-1])
    previous_low = min(lows[:-1])

    score = 0
    signal = "NEUTRAL"
    reasons = []

    if last_close > previous_high:
        signal = "BULLISH"
        score = 4
        reasons.append("Bullish Break of Structure")

    elif last_close < previous_low:
        signal = "BEARISH"
        score = -4
        reasons.append("Bearish Break of Structure")

    confidence = min(1.0, abs(score) / 5)

    return EngineResult(
        name="BOS",
        signal=signal,
        score=score,
        confidence=confidence,
        weight=1.15,
        reasons=reasons,
        metadata={
            "previous_high": previous_high,
            "previous_low": previous_low,
            "last_close": last_close
        }
    ).to_dict()
