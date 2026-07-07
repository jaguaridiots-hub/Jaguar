def _ema(values, period):
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

    if ema20 > ema50 > ema100 > ema200:
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
        "trend": trend
    }


def ema_value(closes, period):
    return _ema(closes, period)
