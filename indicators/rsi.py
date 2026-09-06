def rsi(candles):
    closes = [c["close"] for c in candles]

    period = 14

    gains = []
    losses = []

    for i in range(1, len(closes)):
        diff = closes[i] - closes[i-1]

        gains.append(max(diff,0))
        losses.append(abs(min(diff,0)))

    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period

    if avg_loss == 0:
        value = 100
    else:
        rs = avg_gain / avg_loss
        value = 100 - (100/(1+rs))

    if value > 70:
        signal = "OVERBOUGHT"
    elif value < 30:
        signal = "OVERSOLD"
    else:
        signal = "NEUTRAL"

    print("====== RSI ======")
    print(value)
    print(signal)

    return {
        "value": value,
        "signal": signal
    }
