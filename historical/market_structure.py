def market_structure(candles):

    highs = [c["high"] for c in candles[-20:]]
    lows = [c["low"] for c in candles[-20:]]

    hh = highs[-1] > max(highs[:-1])
    ll = lows[-1] < min(lows[:-1])

    if hh:
        return "Higher High"

    if ll:
        return "Lower Low"

    if candles[-1]["close"] > candles[-10]["close"]:
        return "Uptrend"

    if candles[-1]["close"] < candles[-10]["close"]:
        return "Downtrend"

    return "Range"
