def break_of_structure(candles, lookback=20):

    highs = [c["high"] for c in candles[-lookback:]]
    lows = [c["low"] for c in candles[-lookback:]]

    last = candles[-1]

    if last["close"] > max(highs[:-1]):
        return "Bullish BOS"

    if last["close"] < min(lows[:-1]):
        return "Bearish BOS"

    return "No BOS"


def change_of_character(candles):

    if len(candles) < 60:
        return "Unknown"

    recent = candles[-1]["close"]
    old = candles[-30]["close"]

    if recent > old:
        return "Bullish CHoCH"

    if recent < old:
        return "Bearish CHoCH"

    return "Neutral"
