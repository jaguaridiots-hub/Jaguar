class GannConfluence:

    @staticmethod
    def calculate(price_data, angle_data, time_data):

        score = 0
        reasons = []

        # Angle Analysis
        if angle_data["angle"] == "1x1 BULLISH":
            score += 40
            reasons.append("Bullish Gann Angle")

        elif angle_data["angle"] == "1x1 BEARISH":
            score -= 40
            reasons.append("Bearish Gann Angle")

        # Time Cycle Analysis
        if time_data["signal"] == "MAJOR TURN":
            score += 40
            reasons.append("Major Time Cycle")

        elif time_data["signal"] == "WATCH":
            score += 20
            reasons.append("Important Time Cycle")

        # Price Position
        if price_data["bias"] == "BULLISH":
            score += 20
            reasons.append("Price Above Gann Support")

        elif price_data["bias"] == "BEARISH":
            score -= 20
            reasons.append("Price Near Resistance")

        # Final Decision
        if score >= 60:
            signal = "STRONG BUY"

        elif score >= 20:
            signal = "BUY"

        elif score <= -60:
            signal = "STRONG SELL"

        elif score <= -20:
            signal = "SELL"

        else:
            signal = "NEUTRAL"

        return {
            "score": score,
            "signal": signal,
            "reasons": reasons
        }
