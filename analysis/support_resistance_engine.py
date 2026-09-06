from data.market_data import get_klines

LOOKBACK = 50

def support_resistance():

    candles = get_klines(limit=LOOKBACK)

    highs = [c["high"] for c in candles]
    lows = [c["low"] for c in candles]

    return {
        "support": min(lows),
        "resistance": max(highs)
    }
