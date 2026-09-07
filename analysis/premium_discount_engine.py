from data.market_data import get_klines

def premium_discount_score():
    candles = get_klines(limit=50)

    high = max(c["high"] for c in candles)
    low = min(c["low"] for c in candles)
    current = candles[-1]["close"]

    midpoint = (high + low) / 2

    score = 0
    reasons = []

    if current < midpoint:
        score += 2
        reasons.append("Discount Zone")

    elif current > midpoint:
        score -= 2
        reasons.append("Premium Zone")

    return score, reasons
