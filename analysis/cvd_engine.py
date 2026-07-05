from data.market_data import get_klines

def cvd_score():
    candles = get_klines(limit=100)

    score = 0
    reasons = []

    delta = 0

    for c in candles:
        o = float(c["open"])
        cl = float(c["close"])
        vol = float(c["volume"])

        if cl > o:
            delta += vol
        else:
            delta -= vol

    if delta > 0:
        score += 2
        reasons.append("Bullish CVD")
    else:
        score -= 2
        reasons.append("Bearish CVD")

    return score, reasons
