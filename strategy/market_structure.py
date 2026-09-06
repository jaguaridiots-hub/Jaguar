class MarketStructure:

    @staticmethod
    def detect(candles):

        if len(candles) < 10:
            return {
                "trend": "UNKNOWN",
                "bos": False,
                "choch": False
            }

        highs = [c["high"] for c in candles[-10:]]
        lows = [c["low"] for c in candles[-10:]]

        last_high = highs[-1]
        prev_high = highs[-2]

        last_low = lows[-1]
        prev_low = lows[-2]

        bos = False
        choch = False

        if last_high > prev_high and last_low > prev_low:
            trend = "BULLISH"

        elif last_high < prev_high and last_low < prev_low:
            trend = "BEARISH"

        else:
            trend = "SIDEWAYS"

        if last_high > max(highs[:-1]):
            bos = True

        if last_low < min(lows[:-1]):
            choch = True

        return {
            "trend": trend,
            "bos": bos,
            "choch": choch
        }
