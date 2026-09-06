from data.market_data import candles

high = max(c["high"] for c in candles[-20:])
low = min(c["low"] for c in candles[-20:])
current = candles[-1]["close"]

equilibrium = (high + low) / 2

print("====== Premium / Discount ======")
print(f"High        : {high:.2f}")
print(f"Low         : {low:.2f}")
print(f"Current     : {current:.2f}")
print(f"Equilibrium : {equilibrium:.2f}")

if current > equilibrium:
    print("\nZone : PREMIUM")
else:
    print("\nZone : DISCOUNT")

