def adx(candles):

    highs = [c["high"] for c in candles]
    lows = [c["low"] for c in candles]

    strength = (max(highs[-14:]) - min(lows[-14:]))

    if strength > 1500:
        signal = "STRONG"

    elif strength > 700:
        signal = "MEDIUM"

    else:
        signal = "WEAK"

    return {
        "value": round(strength, 2),
        "signal": signal
    }
