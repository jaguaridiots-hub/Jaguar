from data.market_data import get_klines

def smt_score():
    candles = get_klines(limit=6)

    score = 0
    reasons = []

    highs = [float(c["high"]) for c in candles[-4:]]
    lows = [float(c["low"]) for c in candles[-4:]]

    # Simplified SMT divergence
    if highs[-1] < max(highs[:-1]) and lows[-1] > min(lows[:-1]):
        score += 2
        reasons.append("Bullish SMT")

    elif lows[-1] > min(lows[:-1]) and highs[-1] < max(highs[:-1]):
        score -= 2
        reasons.append("Bearish SMT")

    return score, reasons
