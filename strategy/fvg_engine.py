class FVGEngine:

    @staticmethod
    def analyze(candles):

        signal = "NONE"
        score = 0
        reasons = []

        if len(candles) < 3:
            return {
                "signal": signal,
                "score": score,
                "reasons": reasons
            }

        c1 = candles[-3]
        c2 = candles[-2]
        c3 = candles[-1]

        # Bullish FVG
        if c1["high"] < c3["low"]:

            signal = "BULLISH"

            score = 20

            reasons.append("Bullish Fair Value Gap")

        # Bearish FVG
        elif c1["low"] > c3["high"]:

            signal = "BEARISH"

            score = -20

            reasons.append("Bearish Fair Value Gap")

        return {
            "signal": signal,
            "score": score,
            "reasons": reasons
        }
