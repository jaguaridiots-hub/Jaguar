from indicators.ema import ema20, ema50, ema100, ema200
from indicators.rsi import rsi
import indicators.volume as volume

score = 0

if ema20 > ema50 > ema100 > ema200:
    score += 3

if 45 < rsi < 70:
    score += 2

if volume.signal == "HIGH VOLUME":
    score += 2

if score >= 6:
    signal = "STRONG BUY"
elif score >= 4:
    signal = "BUY"
elif score >= 2:
    signal = "WAIT"
else:
    signal = "SELL"

print("====== Jaguar AI Decision ======")
print("Score :", score)
print("Signal:", signal)
