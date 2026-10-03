class MarketRegimeEngine:

    @staticmethod
    def analyze(candles):

        if len(candles) < 50:
            return {
                "regime": "UNKNOWN",
                "signal": "WAIT",
                "score": 0,
                "reasons": ["Not enough candles"]
            }

        closes = [c["close"] for c in candles[-50:]]

        sma20 = sum(closes[-20:]) / 20
        sma50 = sum(closes) / 50

        last = closes[-1]

        high = max(closes)
        low = min(closes)

        volatility = (high - low) / low

        reasons = []

        if last > sma20 > sma50:
            regime = "TRENDING_BULLISH"
            signal = "BUY"
            score = 25
            reasons.append("Bullish trend")

        elif last < sma20 < sma50:
            regime = "TRENDING_BEARISH"
            signal = "SELL"
            score = -25
            reasons.append("Bearish trend")

        else:
            regime = "RANGING"
            signal = "WAIT"
            score = 0
            reasons.append("Sideways market")

        if volatility > 0.08:
            reasons.append("High volatility")
        else:
            reasons.append("Normal volatility")

        return {
            "regime": regime,
            "signal": signal,
            "score": score,
            "volatility": round(volatility, 4),
            "reasons": reasons,
        }
