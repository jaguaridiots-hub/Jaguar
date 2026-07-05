from historical.data_loader import load_data
from historical.indicators import calculate_indicators
from historical.confluence import *

candles = load_data()

ind = calculate_indicators(candles)

close = candles[-1]["close"]

sr = support_resistance(candles)

gann = gann_levels(close)

fib = fibonacci_confluence(close, ind["fib"])

trend = trend_strength(
    ind["ema20"],
    ind["ema50"],
    ind["ema200"]
)

print("\n======= JAGUAR CONFLUENCE =======\n")

print("Current Price :", close)
print("Support :", sr["support"])
print("Resistance :", sr["resistance"])
print("Trend Score :", trend)
print("Nearest Fib :", fib)
print("Gann Levels :")

for g in gann:
    print(g)
