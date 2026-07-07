def fibonacci(candles):
    high = max(c["high"] for c in candles[-100:])
    low = min(c["low"] for c in candles[-100:])

    diff = high - low

    levels = {
        "0.0%": high,
        "23.6%": high - diff * 0.236,
        "38.2%": high - diff * 0.382,
        "50.0%": high - diff * 0.5,
        "61.8%": high - diff * 0.618,
        "78.6%": high - diff * 0.786,
        "100.0%": low
    }

    print("====== Fibonacci ======")
    for k, v in levels.items():
        print(f"{k}: {v:.2f}")

    return levels
