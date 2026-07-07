def atr(candles, period=14):

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

    value = sum(trs[-period:]) / period

    return {
        "value": round(value, 2),
        "volatility": (
            "HIGH"
            if value > (sum(trs) / len(trs))
            else "LOW"
        )
    }
