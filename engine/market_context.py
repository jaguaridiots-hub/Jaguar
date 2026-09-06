from indicators.ema import ema20, ema50, ema100, ema200
from indicators.rsi import rsi

print("\n====== Jaguar Market Context ======\n")

# Trend
if ema20 > ema50 > ema100 > ema200:
    trend = "STRONG BULL"
elif ema20 < ema50 < ema100 < ema200:
    trend = "STRONG BEAR"
else:
    trend = "SIDEWAYS"

# RSI Context
if rsi >= 80:
    phase = "BUY CLIMAX"
    action = "WAIT FOR PULLBACK"
elif rsi >= 60:
    phase = "HEALTHY TREND"
    action = "BUY ON DIP"
elif rsi >= 40:
    phase = "RANGE"
    action = "WAIT"
elif rsi >= 20:
    phase = "PULLBACK"
    action = "LOOK FOR BUY"
else:
    phase = "CAPITULATION"
    action = "WATCH FOR REVERSAL"

print("Trend          :", trend)
print("Market Phase   :", phase)
print("Recommended    :", action)
