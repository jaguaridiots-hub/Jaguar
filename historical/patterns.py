def detect_pattern(candles):

    last = candles[-1]
    prev = candles[-2]

    o = last["open"]
    h = last["high"]
    l = last["low"]
    c = last["close"]

    po = prev["open"]
    pc = prev["close"]

    body = abs(c - o)
    upper = h - max(o, c)
    lower = min(o, c) - l

    # Bullish Engulfing
    if (
        pc < po and
        c > o and
        o < pc and
        c > po
    ):
        return "Bullish Engulfing"

    # Bearish Engulfing
    if (
        pc > po and
        c < o and
        o > pc and
        c < po
    ):
        return "Bearish Engulfing"

    # Hammer
    if lower > body * 2 and upper < body:
        return "Hammer"

    # Shooting Star
    if upper > body * 2 and lower < body:
        return "Shooting Star"

    # Doji
    if body < (h - l) * 0.1:
        return "Doji"

    return "No Pattern"
