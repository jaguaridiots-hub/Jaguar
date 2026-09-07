from historical.data_loader import load_data
from historical.indicators import ema, atr, rsi, volume_sma

candles = load_data()

closes = [c["close"] for c in candles]

print("\n========== JAGUAR V6 INDICATORS ==========\n")

print("EMA20      :", round(ema(closes,20),2))
print("EMA50      :", round(ema(closes,50),2))
print("EMA200     :", round(ema(closes,200),2))
print("ATR14      :", round(atr(candles),2))
print("RSI14      :", round(rsi(closes),2))
print("Volume SMA :", round(volume_sma(candles),2))
