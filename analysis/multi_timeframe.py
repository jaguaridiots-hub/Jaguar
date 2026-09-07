from data.market_data import get_klines
from indicators.ema import ema

TIMEFRAMES = {
    "15m": "15m",
    "1h": "1h",
    "4h": "4h",
    "1d": "1d"
}

def trend(tf):
    candles = get_klines(interval=TIMEFRAMES[tf], limit=250)

    closes = [c["close"] for c in candles]

    ema20 = ema(closes, 20)
    ema50 = ema(closes, 50)
    ema100 = ema(closes, 100)
    ema200 = ema(closes, 200)

    if ema20 > ema50 > ema100 > ema200:
        return "BULLISH"

    if ema20 < ema50 < ema100 < ema200:
        return "BEARISH"

    return "SIDEWAYS"


def report():

    print("\n====== MULTI TIMEFRAME ======\n")

    result = {}

    for tf in TIMEFRAMES:

        t = trend(tf)

        result[tf] = t

        print(f"{tf:5} : {t}")

    return result
