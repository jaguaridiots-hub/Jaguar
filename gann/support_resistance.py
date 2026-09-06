from data.market_data import candles

price = candles[-1]["close"]

print("====== Gann Support & Resistance ======")
print("Current Price :", round(price, 2))
print()

supports = [
    round(price * 0.98, 2),
    round(price * 0.95, 2),
    round(price * 0.92, 2)
]

resistances = [
    round(price * 1.02, 2),
    round(price * 1.05, 2),
    round(price * 1.08, 2)
]

print("Supports")
for s in supports:
    print("-", s)

print()
print("Resistances")
for r in resistances:
    print("-", r)
