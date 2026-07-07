class DecisionEngine:

    @staticmethod
    def analyze(ind, sr):

        score = 0
        reasons = []

        ema = ind["ema"]
        rsi = ind["rsi"]
        volume = ind["volume"]

        # EMA Trend
        if ema["trend"] == "BULLISH":
            score += 30
            reasons.append("Bullish Trend")

        elif ema["trend"] == "BEARISH":
            score -= 30
            reasons.append("Bearish Trend")

        else:
            reasons.append("Sideways Trend")

        # RSI
        if 45 <= rsi["value"] <= 65:
            score += 20
            reasons.append("Healthy RSI")

        elif rsi["value"] < 30:
            score += 15
            reasons.append("Oversold")

        elif rsi["value"] > 70:
            score -= 15
            reasons.append("Overbought")

        # Volume
        if volume["signal"] == "VERY HIGH VOLUME":
            score += 30
            reasons.append("Very High Volume")

        elif volume["signal"] == "HIGH VOLUME":
            score += 20
            reasons.append("High Volume")

        else:
            reasons.append("Low Volume")

        # Market Structure
        if sr["state"] == "BREAKOUT":
            score += 20
            reasons.append("Breakout")

        elif sr["state"] == "BREAKDOWN":
            score -= 20
            reasons.append("Breakdown")

        else:
            reasons.append("Range Market")

        # Confidence
        confidence = min(abs(score), 100)

        # Final Signal
        if score >= 60:
            signal = "BUY"

        elif score <= -60:
            signal = "SELL"

        else:
            signal = "NO TRADE"

        return {
            "signal": signal,
            "confidence": confidence,
            "score": score,
            "reasons": reasons
        }
