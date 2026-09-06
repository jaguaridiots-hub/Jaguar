from math import sqrt

def bollinger(candles):

    closes = [c["close"] for c in candles]

    period = 20

    data = closes[-period:]

    sma = sum(data) / period

    variance = sum((x - sma) ** 2 for x in data) / period

    std = sqrt(variance)

    upper = sma + 2 * std
    lower = sma - 2 * std

    last = closes[-1]

    if last > upper:
        signal = "OVERBOUGHT"
    elif last < lower:
        signal = "OVERSOLD"
    else:
        signal = "NORMAL"

    return {
        "upper": round(upper, 2),
        "middle": round(sma, 2),
        "lower": round(lower, 2),
        "signal": signal
    }
