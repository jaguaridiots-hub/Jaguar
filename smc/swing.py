from data.market_data import candles

lookback = 20

highs = [c["high"] for c in candles[-lookback:]]
lows = [c["low"] for c in candles[-lookback:]]

swing_high = max(highs)
swing_low = min(lows)

current = candles[-1]["close"]

print("====== Swing Detection ======")
print(f"Swing High : {swing_high:.2f}")
print(f"Swing Low  : {swing_low:.2f}")
print(f"Current    : {current:.2f}")

if current > (swing_high + swing_low) / 2:
    print("Trend : UP")
else:
    print("Trend : DOWN")
