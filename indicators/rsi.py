from data.market_data import candles

period = 14

closes = [c["close"] for c in candles]

gains = []
losses = []

for i in range(1, len(closes)):
    diff = closes[i] - closes[i-1]
    if diff > 0:
        gains.append(diff)
        losses.append(0)
    else:
        gains.append(0)
        losses.append(abs(diff))

avg_gain = sum(gains[-period:]) / period
avg_loss = sum(losses[-period:]) / period

if avg_loss == 0:
    rsi = 100
else:
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

print("====== RSI ======")
print(f"Value : {rsi:.2f}")

if rsi > 70:
    print("Signal : OVERBOUGHT")
elif rsi < 30:
    print("Signal : OVERSOLD")
else:
    print("Signal : NEUTRAL")
