from data.market_data import get_klines

def inducement_score():
    candles = get_klines(limit=6)

    score = 0
    reasons = []

    h1 = float(candles[-4]["high"])
    h2 = float(candles[-3]["high"])
    h3 = float(candles[-2]["high"])

    l1 = float(candles[-4]["low"])
    l2 = float(candles[-3]["low"])
    l3 = float(candles[-2]["low"])

    # Bullish inducement
    if l2 < l1 and h3 > h2:
        score += 2
        reasons.append("Bullish Inducement")

    # Bearish inducement
    elif h2 > h1 and l3 < l2:
        score -= 2
        reasons.append("Bearish Inducement")

    return score, reasons
