from data.market_data import get_klines

def volume_profile_score():

    candles = get_klines(limit=200)

    poc = max(candles, key=lambda x: float(x["volume"]))
    poc_price = float(poc["close"])

    current = float(candles[-1]["close"])

    score = 0
    reasons = []

    if current > poc_price:
        score += 2
        reasons.append("Above POC")
    else:
        score -= 2
        reasons.append("Below POC")

    return score, reasons
