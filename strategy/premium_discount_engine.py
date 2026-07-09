class PremiumDiscountEngine:

    @staticmethod
    def analyze(candles):

        highs = [c["high"] for c in candles[-100:]]
        lows = [c["low"] for c in candles[-100:]]

        swing_high = max(highs)
        swing_low = min(lows)

        equilibrium = (swing_high + swing_low) / 2

        price = candles[-1]["close"]

        if price > equilibrium:
            return {
                "zone": "PREMIUM",
                "score": -10,
                "equilibrium": equilibrium,
                "high": swing_high,
                "low": swing_low,
                "reasons": ["Price in Premium Zone"]
            }

        elif price < equilibrium:
            return {
                "zone": "DISCOUNT",
                "score": 10,
                "equilibrium": equilibrium,
                "high": swing_high,
                "low": swing_low,
                "reasons": ["Price in Discount Zone"]
            }

        return {
            "zone": "EQUILIBRIUM",
            "score": 0,
            "equilibrium": equilibrium,
            "high": swing_high,
            "low": swing_low,
            "reasons": []
        }
