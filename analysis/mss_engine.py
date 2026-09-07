from data.market_data import get_klines

def mss_score():
    candles = get_klines(limit=6)

    score = 0
    reasons = []

    h1 = candles[-6]["high"]
    h2 = candles[-5]["high"]
    h3 = candles[-4]["high"]

    l1 = candles[-6]["low"]
    l2 = candles[-5]["low"]
    l3 = candles[-4]["low"]

    if h3 > h2 > h1:
        score += 2
        reasons.append("Bullish MSS")

    elif l3 < l2 < l1:
        score -= 2
        reasons.append("Bearish MSS")

    return score, reasons
