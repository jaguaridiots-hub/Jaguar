from data.market_data import get_klines

def bos_score():
    candles = get_klines(limit=30)

    highs = [c["high"] for c in candles]
    lows = [c["low"] for c in candles]

    score = 0
    reasons = []

    if highs[-1] > max(highs[:-1]):
        score += 2
        reasons.append("Bullish BOS")

    if lows[-1] < min(lows[:-1]):
        score -= 2
        reasons.append("Bearish BOS")

    return score, reasons
