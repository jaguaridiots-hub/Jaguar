from indicators.ema import ema_value


def macd(candles):

    closes = [c["close"] for c in candles]

    ema12 = ema_value(closes, 12)
    ema26 = ema_value(closes, 26)

    macd_line = ema12 - ema26

    signal = "BUY"

    if macd_line < 0:
        signal = "SELL"

    if abs(macd_line) < 20:
        signal = "NEUTRAL"

    return {
        "macd": round(macd_line, 2),
        "signal": signal
    }
