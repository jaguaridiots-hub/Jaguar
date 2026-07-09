class BOSEngine:

    @staticmethod
    def analyze(candles):

        highs = [c["high"] for c in candles[-20:]]
        lows = [c["low"] for c in candles[-20:]]

        last = candles[-1]

        signal = "NONE"

        if last["close"] > max(highs[:-1]):
            signal = "BULLISH_BOS"

        elif last["close"] < min(lows[:-1]):
            signal = "BEARISH_BOS"

        return {
            "signal": signal,
            "high": max(highs),
            "low": min(lows)
        }
