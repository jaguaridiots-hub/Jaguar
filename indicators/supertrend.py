def supertrend(candles):

    closes = [c["close"] for c in candles]

    sma = sum(closes[-10:]) / 10
    last = closes[-1]

    if last > sma:
        trend = "BULLISH"
    elif last < sma:
        trend = "BEARISH"
    else:
        trend = "SIDEWAYS"

    return {
        "value": round(sma, 2),
        "trend": trend,
        "signal": trend
    }
