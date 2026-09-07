from data.market_data import get_klines

def vwap_score():
    candles = get_klines(limit=100)

    score = 0
    reasons = []

    total_pv = 0
    total_vol = 0

    for c in candles:
        high = float(c["high"])
        low = float(c["low"])
        close = float(c["close"])
        volume = float(c["volume"])

        typical = (high + low + close) / 3

        total_pv += typical * volume
        total_vol += volume

    if total_vol == 0:
        return score, reasons

    vwap = total_pv / total_vol
    price = float(candles[-1]["close"])

    if price > vwap:
        score += 2
        reasons.append("Above VWAP")

    else:
        score -= 2
        reasons.append("Below VWAP")

    return score, reasons
