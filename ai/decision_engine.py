class AIDecision:

    @staticmethod
    def decide(score):

        s = score["score"]

        if s >= 60:
            signal = "STRONG BUY"

        elif s >= 30:
            signal = "BUY"

        elif s <= -60:
            signal = "STRONG SELL"

        elif s <= -30:
            signal = "SELL"

        else:
            signal = "HOLD"

        return {
            "signal": signal,
            "score": score["score"],
            "confidence": score["confidence"],
            "reasons": score["reasons"]
        }
