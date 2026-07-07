from core.engine_result import EngineResult
from data.market_data import candles


def analyze(state):

    if len(candles) < 20:
        return EngineResult(
            name="Liquidity",
            signal="NEUTRAL",
            score=0,
            confidence=0,
            weight=1.10,
            reasons=["Not enough candles"]
        ).to_dict()

    highs = [c["high"] for c in candles[-20:]]
    lows = [c["low"] for c in candles[-20:]]

    last = candles[-1]

    prev_high = max(highs[:-1])
    prev_low = min(lows[:-1])

    signal = "NEUTRAL"
    score = 0
    reasons = []

    if last["high"] > prev_high and last["close"] < prev_high:
        signal = "BEARISH"
        score = -3
        reasons.append("Buy-side Liquidity Sweep")

    elif last["low"] < prev_low and last["close"] > prev_low:
        signal = "BULLISH"
        score = 3
        reasons.append("Sell-side Liquidity Sweep")

    confidence = min(1.0, abs(score) / 4)

    return EngineResult(
        name="Liquidity",
        signal=signal,
        score=score,
        confidence=confidence,
        weight=1.10,
        reasons=reasons,
        metadata={
            "previous_high": prev_high,
            "previous_low": prev_low,
            "last_close": last["close"]
        }
    ).to_dict()
