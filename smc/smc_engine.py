from data.market_data import get_klines

LOOKBACK = 5


def swing_high(candles, i):
    high = candles[i]["high"]

    for j in range(i - LOOKBACK, i + LOOKBACK + 1):
        if j == i:
            continue
        if candles[j]["high"] >= high:
            return False

    return True


def swing_low(candles, i):
    low = candles[i]["low"]

    for j in range(i - LOOKBACK, i + LOOKBACK + 1):
        if j == i:
            continue
        if candles[j]["low"] <= low:
            return False

    return True


def detect_structure(candles):
    swing_highs = []
    swing_lows = []

    for i in range(LOOKBACK, len(candles) - LOOKBACK):

        if swing_high(candles, i):
            swing_highs.append((i, candles[i]["high"]))

        if swing_low(candles, i):
            swing_lows.append((i, candles[i]["low"]))

    return swing_highs, swing_lows


def smc_score():

    candles = get_klines(limit=300)

    score = 0
    reasons = []

    highs, lows = detect_structure(candles)

    if len(highs) < 2 or len(lows) < 2:
        return score, reasons

    last_close = candles[-1]["close"]

    previous_high = highs[-2][1]
    latest_high = highs[-1][1]

    previous_low = lows[-2][1]
    latest_low = lows[-1][1]

    # -----------------------
    # Bullish BOS
    # -----------------------
    if last_close > latest_high:
        score += 2
        reasons.append("Bullish BOS")

    # -----------------------
    # Bearish BOS
    # -----------------------
    elif last_close < latest_low:
        score -= 2
        reasons.append("Bearish BOS")

    # -----------------------
    # Bullish CHoCH
    # -----------------------
    if latest_low > previous_low:
        score += 2
        reasons.append("Bullish CHoCH")

    # -----------------------
    # Bearish CHoCH
    # -----------------------
    elif latest_high < previous_high:
        score -= 2
        reasons.append("Bearish CHoCH")

    # -----------------------
    # Fair Value Gap
    # -----------------------
    c1 = candles[-3]
    c2 = candles[-2]
    c3 = candles[-1]

    if c1["high"] < c3["low"]:
        score += 1
        reasons.append("Bullish FVG")

    elif c1["low"] > c3["high"]:
        score -= 1
        reasons.append("Bearish FVG")

    return score, reasons
