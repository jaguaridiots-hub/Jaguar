# indicators/atr.py

def atr(candles, period=14):

    if len(candles) < period + 1:
        return {
            "value": None,
            "ready": False,
            "reason": f"Insufficient candles for ATR (need {period + 1}, got {len(candles)})"
        }

    trs = []

    for i in range(1, len(candles)):
        high = candles[i]["high"]
        low = candles[i]["low"]
        prev_close = candles[i-1]["close"]

        tr = max(
            high - low,
            abs(high - prev_close),
            abs(low - prev_close)
        )

        trs.append(tr)

    avg_tr = sum(trs[-period:]) / period

    return {
        "value": round(avg_tr, 2),
        "volatility": (
            "HIGH"
            if avg_tr > (sum(trs) / len(trs))
            else "LOW"
        )
    }
