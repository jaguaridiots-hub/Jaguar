class GannEngine:

    @staticmethod
    def score(square, angle, time, confluence):

        score = 0
        reasons = []

        # Confluence score
        score += confluence["score"]

        # Angle
        if angle["angle"] == "1x1 BULLISH":
            reasons.append("Bullish Gann Angle")

        elif angle["angle"] == "1x1 BEARISH":
            reasons.append("Bearish Gann Angle")

        # Time
        if time["signal"] == "MAJOR TURN":
            reasons.append("Major Gann Cycle")

        elif time["signal"] == "WATCH":
            reasons.append("Watch Gann Cycle")

        # Price Bias
        reasons.append(square["bias"])

        if score >= 80:
            signal = "STRONG BUY"

        elif score >= 40:
            signal = "BUY"

        elif score <= -80:
            signal = "STRONG SELL"

        elif score <= -40:
            signal = "SELL"

        else:
            signal = "HOLD"

        return {
            "score": score,
            "signal": signal,
            "reasons": reasons
        }
