from data.market_data import get_klines

def breaker_score():
    candles = get_klines(limit=20)

    score = 0
    reasons = []

    last = candles[-1]
    prev = candles[-2]

    # Bullish Breaker
    if last["close"] > prev["high"]:
        score += 2
        reasons.append("Bullish Breaker")

    # Bearish Breaker
    elif last["close"] < prev["low"]:
        score -= 2
        reasons.append("Bearish Breaker")

    return score, reasons
