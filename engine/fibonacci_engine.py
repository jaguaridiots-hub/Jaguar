from core.engine_result import EngineResult
from data.market_data import candles


def analyze(state):

    if len(candles) < 100:
        return EngineResult(
            name="Fibonacci",
            signal="NEUTRAL",
            score=0,
            confidence=0,
            weight=1.10,
            reasons=["Not enough candles"]
        ).to_dict()

    highs = [c["high"] for c in candles[-100:]]
    lows = [c["low"] for c in candles[-100:]]

    swing_high = max(highs)
    swing_low = min(lows)

    diff = swing_high - swing_low

    fib236 = swing_high - diff * 0.236
    fib382 = swing_high - diff * 0.382
    fib500 = swing_high - diff * 0.500
    fib618 = swing_high - diff * 0.618
    fib786 = swing_high - diff * 0.786

    ext127 = swing_high + diff * 0.272
    ext161 = swing_high + diff * 0.618
    ext261 = swing_high + diff * 1.618

    price = state.price

    signal = "NEUTRAL"
    score = 0
    reasons = []

    if fib500 <= price <= fib618:
        signal = "BULLISH"
        score = 3
        reasons.append("Golden Zone")

    elif fib382 <= price <= fib500:
        signal = "BULLISH"
        score = 2
        reasons.append("Bullish Retracement")

    elif price > fib236:
        signal = "BULLISH"
        score = 1
        reasons.append("Above Fib 23.6")

    if price > fib618:
        score += 1
        reasons.append("Strong Recovery")

    confidence = min(1.0, abs(score) / 4)

    return EngineResult(
        name="Fibonacci",
        signal=signal,
        score=score,
        confidence=confidence,
        weight=1.10,
        reasons=reasons,
        metadata={
            "fib236": round(fib236, 2),
            "fib382": round(fib382, 2),
            "fib500": round(fib500, 2),
            "fib618": round(fib618, 2),
            "fib786": round(fib786, 2),
            "extension127": round(ext127, 2),
            "extension161": round(ext161, 2),
            "extension261": round(ext261, 2),
            "swing_high": round(swing_high, 2),
            "swing_low": round(swing_low, 2),
        }
    ).to_dict()
