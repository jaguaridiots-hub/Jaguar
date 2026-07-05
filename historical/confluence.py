import math

def support_resistance(candles, lookback=50):

    highs = [c["high"] for c in candles[-lookback:]]
    lows = [c["low"] for c in candles[-lookback:]]

    resistance = max(highs)
    support = min(lows)

    return {
        "support": round(support, 2),
        "resistance": round(resistance, 2)
    }


def gann_levels(price):

    root = math.sqrt(price)

    levels = []

    for angle in [0.125, 0.25, 0.5, 0.75, 1]:

        value = (root + angle) ** 2

        levels.append(round(value, 2))

    return levels


def fibonacci_confluence(price, fib):

    nearest = None
    distance = 999999

    for level in fib.values():

        d = abs(price - level)

        if d < distance:
            distance = d
            nearest = level

    return {
        "nearest_fib": nearest,
        "distance": round(distance, 2)
    }


def trend_strength(ema20, ema50, ema200):

    score = 0

    if ema20 > ema50:
        score += 30

    if ema50 > ema200:
        score += 40

    if ema20 > ema200:
        score += 30

    return score
