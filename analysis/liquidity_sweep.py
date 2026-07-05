from data.market_data import get_klines

def liquidity_sweep_score():
    candles = get_klines(limit=10)

    score = 0
    reasons = []

    last = candles[-1]
    prev = candles[-2]

    if float(last["high"]) > float(prev["high"]) and float(last["close"]) < float(prev["high"]):
        score -= 2
        reasons.append("Buy Side Liquidity Swept")

    if float(last["low"]) < float(prev["low"]) and float(last["close"]) > float(prev["low"]):
        score += 2
        reasons.append("Sell Side Liquidity Swept")

    return score, reasons
