from data.market_data import candles

high = max(c["high"] for c in candles[-100:])
low = min(c["low"] for c in candles[-100:])

diff = high - low

levels = {
    "0.0%": high,
    "23.6%": high - diff * 0.236,
    "38.2%": high - diff * 0.382,
    "50.0%": high - diff * 0.500,
    "61.8%": high - diff * 0.618,
    "78.6%": high - diff * 0.786,
    "100.0%": low
}

print("====== Fibonacci ======")
print(f"High : {high:.2f}")
print(f"Low  : {low:.2f}")

print()

for level, price in levels.items():
    print(f"{level:>6} : {price:.2f}")
