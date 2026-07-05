from data.market_data import candles

period = 14

trs = []

for i in range(1, len(candles)):
    high = candles[i]["high"]
    low = candles[i]["low"]
    prev_close = candles[i-1]["close"]

    tr = max(
        high - low,
        abs(high - prev_close),
        abs(low - prev_close)
    )

    trs.append(tr)

atr = sum(trs[-period:]) / period

print("====== ATR ======")
print(f"Period : {period}")
print(f"ATR Value : {atr:.2f}")

if atr > 500:
    print("Volatility : HIGH")
elif atr > 200:
    print("Volatility : NORMAL")
else:
    print("Volatility : LOW")
