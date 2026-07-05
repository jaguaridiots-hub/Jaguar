from data.market_data import candles

volumes = [c["volume"] for c in candles]

current = volumes[-1]
average = sum(volumes[-20:]) / 20

print("====== Volume ======")
print(f"Current : {current:.2f}")
print(f"Average : {average:.2f}")

if current > average * 1.5:
    print("Signal : VERY HIGH VOLUME")
elif current > average:
    print("Signal : HIGH VOLUME")
else:
    print("Signal : LOW VOLUME")

if current > average:
    signal = "HIGH VOLUME"
else:
    signal = "LOW VOLUME"

print(f"Current : {current:.2f}")
print(f"Average : {average:.2f}")
print(f"Signal  : {signal}")
