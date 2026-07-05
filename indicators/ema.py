from data.market_data import candles

def ema(data, period):
    k = 2 / (period + 1)
    value = sum(data[:period]) / period

    for price in data[period:]:
        value = price * k + value * (1 - k)

    return round(value, 2)

def calculate_ema(close):
    ema20 = ema(close, 20)
    ema50 = ema(close, 50)
    ema100 = ema(close, 100)
    ema200 = ema(close, 200)

    return ema20, ema50, ema100, ema200


closes = [c["close"] for c in candles]

ema20, ema50, ema100, ema200 = calculate_ema(closes)

print("====== EMA ======")
print("EMA20 :", ema20)
print("EMA50 :", ema50)
print("EMA100:", ema100)
print("EMA200:", ema200)

if ema20 > ema50 > ema100 > ema200:
    print("\nTrend : STRONG BULLISH")
elif ema20 < ema50 < ema100 < ema200:
    print("\nTrend : STRONG BEARISH")
else:
    print("\nTrend : SIDEWAYS")
