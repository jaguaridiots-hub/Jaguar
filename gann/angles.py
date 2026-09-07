from data.market_data import candles

price = candles[-1]["close"]

print("====== Gann Angles ======")
print("Price :", round(price, 2))
print()

angles = {
    "1x8": price * 1.125,
    "1x4": price * 1.25,
    "1x2": price * 1.50,
    "1x1": price * 2.00,
    "2x1": price * 3.00,
    "4x1": price * 5.00,
    "8x1": price * 9.00,
}

for k, v in angles.items():
    print(f"{k:>3} : {v:.2f}")
