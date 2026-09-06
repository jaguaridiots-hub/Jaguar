from data.market_data import get_klines

LOOKBACK = 5

def swing_score():
    candles = get_klines(limit=100)

    score = 0
    reasons = []

    if len(candles) < LOOKBACK * 2 + 1:
        return score, reasons

    highs = [float(c["high"]) for c in candles]
    lows = [float(c["low"]) for c in candles]

    swing_high = None
    swing_low = None

    for i in range(LOOKBACK, len(highs) - LOOKBACK):

        if highs[i] == max(highs[i-LOOKBACK:i+LOOKBACK+1]):
            swing_high = highs[i]

        if lows[i] == min(lows[i-LOOKBACK:i+LOOKBACK+1]):
            swing_low = lows[i]

    current = float(candles[-1]["close"])

    if swing_low and current > swing_low:
        score += 1
        reasons.append("Above Swing Low")

    if swing_high and current < swing_high:
        score += 1
        reasons.append("Below Swing High")

    return score, reasons
