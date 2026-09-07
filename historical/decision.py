from historical.market_structure import market_structure
from historical.confluence import (
    support_resistance,
    gann_levels,
    fibonacci_confluence,
    trend_strength,
)
from historical.patterns import detect_pattern
from historical.smc import smc

def decision(candles):

    ind = calculate_indicators(candles)
    trend = market_structure(candles)
    price = candles[-1]["close"]

    sr = support_resistance(candles)
    gann = gann_levels(price)
    fib = candles[-1]["fib"]
    fib_conf = fibonacci_confluence(price, fib)

    trend = trend_strength(
        indicators["ema20"],
        indicators["ema50"],
        indicators["ema200"]
    )
    smc = analyze_smc(candles)
    pattern = detect_pattern(candles)

    score = 0
    reasons = []

    # Trend
    if trend == "Uptrend":
        score += 20
        reasons.append("Bullish Trend")

    elif trend == "Downtrend":
        score -= 20
        reasons.append("Bearish Trend")

    # EMA
    if ind["ema20"] > ind["ema50"] > ind["ema200"]:
        score += 20
        reasons.append("EMA Alignment")

    elif ind["ema20"] < ind["ema50"] < ind["ema200"]:
        score -= 20
        reasons.append("Bearish EMA")

    # RSI
    if ind["rsi"] > 55:
        score += 15
        reasons.append("Bullish RSI")

    elif ind["rsi"] < 45:
        score -= 15
        reasons.append("Bearish RSI")

    # Volume
    if candles[-1]["volume"] > ind["volume_sma"]:
        score += 10
        reasons.append("High Volume")

    # BOS / CHoCH
    if smc["choch"] == "Bullish":
        score += 20
        reasons.append("Bullish CHoCH")

    if smc["bos"] == "Bullish":
        score += 15
        reasons.append("Bullish BOS")

    # Pattern
    if pattern in ["Bullish Engulfing", "Hammer"]:
        score += 10
        reasons.append(pattern)

    elif pattern in ["Bearish Engulfing", "Shooting Star"]:
        score -= 10
        reasons.append(pattern)

    entry = candles[-1]["close"]
    atr = ind["atr"]

    sl_buy = round(entry - atr, 2)
    tp_buy = round(entry + atr * 2, 2)

    sl_sell = round(entry + atr, 2)
    tp_sell = round(entry - atr * 2, 2)

    confidence = min(abs(score), 100)

    if score >= 60:
        return {
            "signal": "BUY",
            "confidence": confidence,
            "grade": "A+",
            "entry": round(entry, 2),
            "sl": sl_buy,
            "tp": tp_buy,
            "reasons": reasons
        }

    if score <= -60:
        return {
            "signal": "SELL",
            "confidence": confidence,
            "grade": "A+",
            "entry": round(entry, 2),
            "sl": sl_sell,
            "tp": tp_sell,
            "reasons": reasons
        }

    return {
        "signal": "WAIT",
        "confidence": confidence,
        "grade": "B",
        "reasons": reasons
    }
