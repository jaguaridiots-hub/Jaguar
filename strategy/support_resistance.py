class SupportResistance:

    @staticmethod
    def calculate(candles, lookback=50):

        recent = candles[-lookback:]

        support = min(c["low"] for c in recent)
        resistance = max(c["high"] for c in recent)

        current = recent[-1]["close"]

        if current > resistance:
            state = "BREAKOUT"
        elif current < support:
            state = "BREAKDOWN"
        else:
            state = "RANGE"

        return {
            "support": round(support, 2),
            "resistance": round(resistance, 2),
            "state": state
        }
