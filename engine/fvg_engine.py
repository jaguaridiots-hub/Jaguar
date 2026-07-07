from core.engine_result import EngineResult
from data.market_data import candles


def analyze(state):

    if len(candles) < 3:
        return EngineResult(
            name="Fair Value Gap",
            signal="NEUTRAL",
            score=0,
            confidence=0,
            weight=1.15,
            reasons=["Not enough candles"]
        ).to_dict()

    prev2 = candles[-3]
    last = candles[-1]

    signal = "NEUTRAL"
    score = 0
    reasons = []

    bullish_gap = prev2["high"] < last["low"]
    bearish_gap = prev2["low"] > last["high"]

    metadata = {}

    if bullish_gap:

        gap_low = prev2["high"]
        gap_high = last["low"]

        metadata = {
            "gap_low": gap_low,
            "gap_high": gap_high
        }

        if gap_low <= state.price <= gap_high:
            signal = "BULLISH"
            score = 4
            reasons.append("Bullish Fair Value Gap")

    elif bearish_gap:

        gap_low = last["high"]
        gap_high = prev2["low"]

        metadata = {
            "gap_low": gap_low,
            "gap_high": gap_high
        }

        if gap_low <= state.price <= gap_high:
            signal = "BEARISH"
            score = -4
            reasons.append("Bearish Fair Value Gap")

    confidence = min(1.0, abs(score) / 5)

    return EngineResult(
        name="Fair Value Gap",
        signal=signal,
        score=score,
        confidence=confidence,
        weight=1.15,
        reasons=reasons,
        metadata=metadata
    ).to_dict()
