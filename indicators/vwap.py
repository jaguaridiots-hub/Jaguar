def vwap(candles):

    pv = 0
    volume = 0

    for c in candles:
        typical = (c["high"] + c["low"] + c["close"]) / 3
        pv += typical * c["volume"]
        volume += c["volume"]

    value = pv / volume

    last = candles[-1]["close"]

    if last > value:
        signal = "ABOVE VWAP"
    elif last < value:
        signal = "BELOW VWAP"
    else:
        signal = "AT VWAP"

    return {
        "value": round(value,2),
        "signal": signal
    }
