class JaguarBrainV2:

    @staticmethod
    def decide(technical, smc, gann, mtf, risk):

        score = (
            technical["score"] +
            smc["score"] +
            gann["score"] +
            mtf["confidence"] +
            risk["quality"]
        ) / 5

        if score >= 80:
            signal = "STRONG BUY"
        elif score >= 60:
            signal = "BUY"
        elif score <= 20:
            signal = "STRONG SELL"
        elif score <= 40:
            signal = "SELL"
        else:
            signal = "HOLD"

        return {
            "signal": signal,
            "confidence": round(score, 2)
        }
