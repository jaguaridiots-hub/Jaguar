class MasterConfluenceV2:

    @staticmethod
    def analyze(technical, smc, gann, mtf, risk):

        score = (
            technical["score"] * 0.30 +
            smc["score"] * 0.25 +
            gann["score"] * 0.20 +
            mtf["confidence"] * 0.15 +
            risk["quality"] * 0.10
        )

        score = max(-100, min(100, score))

        confidence = round((score + 100) / 2, 2)

        if confidence >= 85:
            signal = "STRONG BUY"

        elif confidence >= 70:
            signal = "BUY"

        elif confidence >= 55:
            signal = "BUY ON RETRACEMENT"

        elif confidence >= 45:
            signal = "WAIT"

        elif confidence >= 30:
            signal = "SELL"

        else:
            signal = "STRONG SELL"

        return {
            "signal": signal,
            "confidence": confidence,
            "score": score
        }
