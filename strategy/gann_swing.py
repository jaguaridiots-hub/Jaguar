class GannSwing:

    @staticmethod
    def calculate(candles):

        if len(candles) < 5:
            return {
                "trend": "UNKNOWN",
                "last_high": None,
                "last_low": None,
                "signal": "NONE"
            }

        highs = [c["high"] for c in candles]
        lows = [c["low"] for c in candles]

        last_high = max(highs[-5:])
        last_low = min(lows[-5:])

        current = candles[-1]["close"]
        previous = candles[-2]["close"]

        if current > previous and current > last_high * 0.995:
            trend = "UPSWING"
            signal = "BUY"

        elif current < previous and current < last_low * 1.005:
            trend = "DOWNSWING"
            signal = "SELL"

        else:
            trend = "SIDEWAYS"
            signal = "HOLD"

        return {
            "trend": trend,
            "last_high": round(last_high, 2),
            "last_low": round(last_low, 2),
            "signal": signal
        }
