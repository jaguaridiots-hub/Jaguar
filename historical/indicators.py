from math import sqrt

def sma(values):
    return sum(values) / len(values)

def ema(candles, period):
    k = 2 / (period + 1)

    ema_value = candles[0]["close"]

    for candle in candles[1:]:
        ema_value = candle["close"] * k + ema_value * (1 - k)

    return round(ema_value, 2)


def atr(candles, period=14):

    trs = []

    for i in range(1, len(candles)):
        high = candles[i]["high"]
        low = candles[i]["low"]
        prev_close = candles[i-1]["close"]

        tr = max(
            high-low,
            abs(high-prev_close),
            abs(low-prev_close)
        )

        trs.append(tr)

    return round(sum(trs[-period:]) / period,2)


def rsi(candles, period=14):

    gains=[]
    losses=[]

    for i in range(-period, -1):

        change = candles[i+1]["close"]-candles[i]["close"]

        if change>0:
            gains.append(change)
            losses.append(0)

        else:
            gains.append(0)
            losses.append(abs(change))

    avg_gain=sma(gains)
    avg_loss=sma(losses)

    if avg_loss==0:
        return 100

    rs=avg_gain/avg_loss

    return round(100-(100/(1+rs)),2)


def volume_sma(candles,period=20):

    return round(
        sma([c["volume"] for c in candles[-period:]]),2
    )


def swing_high(candles,lookback=30):

    return max(c["high"] for c in candles[-lookback:])


def swing_low(candles,lookback=30):

    return min(c["low"] for c in candles[-lookback:])


def fibonacci(high,low):

    diff=high-low

    return{

        "23.6":round(high-diff*0.236,2),

        "38.2":round(high-diff*0.382,2),

        "50":round(high-diff*0.5,2),

        "61.8":round(high-diff*0.618,2),

        "78.6":round(high-diff*0.786,2)
    }


def calculate_indicators(candles):

    high=swing_high(candles)

    low=swing_low(candles)

    return{

        "ema20":ema(candles[-20:],20),

        "ema50":ema(candles[-50:],50),

        "ema200":ema(candles[-200:],200),

        "atr":atr(candles),

        "rsi":rsi(candles),

        "volume_sma":volume_sma(candles),

        "swing_high":high,

        "swing_low":low,

        "fib":fibonacci(high,low)
    }
