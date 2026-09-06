from data.market_data import get_klines

def cisd_score():
    candles = get_klines(limit=5)

    score = 0
    reasons = []

    o1 = float(candles[-2]["open"])
    c1 = float(candles[-2]["close"])

    o2 = float(candles[-1]["open"])
    c2 = float(candles[-1]["close"])

    # Bullish CISD
    if c1 < o1 and c2 > o2 and c2 > o1:
        score += 2
        reasons.append("Bullish CISD")

    # Bearish CISD
    elif c1 > o1 and c2 < o2 and c2 < o1:
        score -= 2
        reasons.append("Bearish CISD")

    return score, reasons
