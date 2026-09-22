def _ema(values, period):
    if not isinstance(values, (list, tuple)):
        raise TypeError("EMA values must be a list or tuple")

    if period <= 0:
        raise ValueError("EMA period must be positive")

    if len(values) < period:
        return None

    k = 2 / (period + 1)
    ema = sum(values[:period]) / period

    for price in values[period:]:
        ema = price * k + ema * (1 - k)

    return round(ema, 2)


def ema(candles):
    closes = [c["close"] for c in candles]

    ema20 = _ema(closes, 20)
    ema50 = _ema(closes, 50)
    ema100 = _ema(closes, 100)
    ema200 = _ema(closes, 200)

    ready = {
        20: ema20 is not None,
        50: ema50 is not None,
        100: ema100 is not None,
        200: ema200 is not None,
    }

    if not all(ready.values()):
        trend = "UNAVAILABLE"
    elif ema20 > ema50 > ema100 > ema200:
        trend = "STRONG BULLISH"
    elif ema20 < ema50 < ema100 < ema200:
        trend = "STRONG BEARISH"
    else:
        trend = "SIDEWAYS"

    return {
        "ema20": ema20,
        "ema50": ema50,
        "ema100": ema100,
        "ema200": ema200,
        "trend": trend,
        "ready": ready,
    }


def ema_value(closes, period):
    return _ema(closes, period)
