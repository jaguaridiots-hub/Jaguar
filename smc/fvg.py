from data.market_data import candles

candle1 = candles[-3]
candle2 = candles[-1]

print("====== Fair Value Gap ======")

print(f"Candle 1 High : {candle1['high']:.2f}")
print(f"Candle 2 Low  : {candle2['low']:.2f}")

if candle2["low"] > candle1["high"]:
    gap = candle2["low"] - candle1["high"]
    print("\nFVG : BULLISH")
    print(f"Gap Size : {gap:.2f}")
elif candle2["high"] < candle1["low"]:
    gap = candle1["low"] - candle2["high"]
    print("\nFVG : BEARISH")
    print(f"Gap Size : {gap:.2f}")
else:
    print("\nFVG : NONE")
