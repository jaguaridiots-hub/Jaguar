from data.market_data import get_klines

def ote_score():
    candles = get_klines(limit=100)

    score = 0
    reasons = []

    highs = [float(c["high"]) for c in candles]
    lows = [float(c["low"]) for c in candles]

    high = max(highs)
    low = min(lows)

    price = float(candles[-1]["close"])

    fib62 = high - (high - low) * 0.62
    fib79 = high - (high - low) * 0.79

    if fib79 <= price <= fib62:
        score += 3
        reasons.append("OTE Entry")

    return score, reasons
