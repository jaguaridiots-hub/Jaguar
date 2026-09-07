from data.market_data import get_klines
from indicators.ema import calculate_ema
TIMEFRAMES = [
    "1m",
    "5m",
    "15m",
    "30m",
    "1h",
    "4h",
    "1d"
]

print("========== Jaguar Multi-Timeframe Scanner ==========\n")

bullish = 0
bearish = 0

for tf in TIMEFRAMES:

    candles = get_klines("BTCUSDT", tf, 300)

    close = [float(c["close"]) for c in candles]

    e20, e50, e100, e200 = calculate_ema(close)

    if e20 > e50 > e100 > e200:
        trend = "BULLISH"
        bullish += 1

    elif e20 < e50 < e100 < e200:
        trend = "BEARISH"
        bearish += 1

    else:
        trend = "NEUTRAL"

    print(f"{tf:>4} : {trend}")

print()

if bullish >= 5:
    overall = "STRONG BUY"

elif bearish >= 5:
    overall = "STRONG SELL"

else:
    overall = "WAIT"

confidence = int(max(bullish, bearish) / len(TIMEFRAMES) * 100)

print("==============================")
print("Overall    :", overall)
print("Confidence :", str(confidence) + "%")
