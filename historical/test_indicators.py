from historical.data_loader import load_data
from historical.indicators import ema, atr

candles = load_data()

closes = [c["close"] for c in candles]

print("\n====== JAGUAR INDICATORS ======\n")

print("EMA20 :", round(ema(closes,20),2))
print("EMA50 :", round(ema(closes,50),2))
print("ATR14 :", round(atr(candles),2))
