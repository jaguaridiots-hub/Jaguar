class MSSEngine:

    @staticmethod
    def analyze(candles):

        highs = [c["high"] for c in candles[-25:]]
        lows = [c["low"] for c in candles[-25:]]

        last = candles[-1]
        prev = candles[-2]

        score = 0
        signal = "NONE"
        reasons = []

        recent_high = max(highs[:-1])
        recent_low = min(lows[:-1])

        if last["close"] > recent_high and prev["close"] <= recent_high:
            signal = "BULLISH_MSS"
            score = 30
            reasons.append("Bullish Market Structure Shift")

        elif last["close"] < recent_low and prev["close"] >= recent_low:
            signal = "BEARISH_MSS"
            score = -30
            reasons.append("Bearish Market Structure Shift")

        return {
            "signal": signal,
            "score": score,
            "recent_high": recent_high,
            "recent_low": recent_low,
            "reasons": reasons
        }
