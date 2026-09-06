from data.market_data import get_klines

LOOKBACK = 20
TOLERANCE = 0.001


def liquidity_score():
    candles = get_klines(limit=300)

    score = 0
    reasons = []

    highs = [c["high"] for c in candles[-LOOKBACK:]]
    lows = [c["low"] for c in candles[-LOOKBACK:]]

    current = candles[-1]
    previous = candles[-2]

    highest = max(highs)
    lowest = min(lows)

    # ==========================
    # Buy Side Liquidity Sweep
    # ==========================
    if (
        current["high"] > highest
        and current["close"] < highest
    ):
        score -= 2
        reasons.append("Buy Side Liquidity Sweep")

    # ==========================
    # Sell Side Liquidity Sweep
    # ==========================
    if (
        current["low"] < lowest
        and current["close"] > lowest
    ):
        score += 2
        reasons.append("Sell Side Liquidity Sweep")

    # ==========================
    # Equal Highs
    # ==========================
    equal_highs = 0

    for h in highs:
        if abs(h - highest) / highest < TOLERANCE:
            equal_highs += 1

    if equal_highs >= 2:
        reasons.append("Equal High Liquidity")

    # ==========================
    # Equal Lows
    # ==========================
    equal_lows = 0

    for l in lows:
        if abs(l - lowest) / lowest < TOLERANCE:
            equal_lows += 1

    if equal_lows >= 2:
        reasons.append("Equal Low Liquidity")

    # ==========================
    # Strong Breakout
    # ==========================
    if current["close"] > highest:
        score += 1
        reasons.append("Liquidity Breakout Up")

    if current["close"] < lowest:
        score -= 1
        reasons.append("Liquidity Breakout Down")

    return score, reasons
