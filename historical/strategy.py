# historical/strategy.py

from historical.indicators import calculate_indicators


def generate_signal(candles):

    if len(candles) < 250:
        return None

    ind = calculate_indicators(candles)

    ema20 = ind["ema20"]
    ema50 = ind["ema50"]
    ema200 = ind["ema200"]
    rsi = ind["rsi"]
    atr = ind["atr"]
    vol_sma = ind["volume_sma"]

    close = candles[-1]["close"]
    volume = candles[-1]["volume"]

    score = 0

    # Trend
    if ema20 > ema50:
        score += 20

    if ema50 > ema200:
        score += 20

    # Momentum
    if rsi >= 50:
        score += 20

    # Volume
    if volume > vol_sma:
        score += 20

    # Volatility
    if atr > 100:
        score += 20

    confidence = score

    # BUY
    if confidence >= 80:

        sl = close - atr
        tp = close + atr * 2

        return {
            "signal": "BUY",
            "entry": round(close, 2),
            "sl": round(sl, 2),
            "tp": round(tp, 2),
            "confidence": confidence,
            "grade": "A+"
        }

    # SELL
    if confidence <= 20:

        sl = close + atr
        tp = close - atr * 2

        return {
            "signal": "SELL",
            "entry": round(close, 2),
            "sl": round(sl, 2),
            "tp": round(tp, 2),
            "confidence": 100 - confidence,
            "grade": "A+"
        }

    # WAIT
    return {
        "signal": "WAIT",
        "confidence": confidence,
        "grade": "B"
    }
