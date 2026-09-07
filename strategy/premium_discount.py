class PremiumDiscount:

    @staticmethod
    def detect(candles):

        if len(candles) < 50:
            return {
                "zone": "UNKNOWN",
                "equilibrium": None
            }

        recent = candles[-50:]

        high = max(c["high"] for c in recent)
        low = min(c["low"] for c in recent)

        equilibrium = (high + low) / 2

        price = recent[-1]["close"]

        if price > equilibrium:
            zone = "PREMIUM"
        elif price < equilibrium:
            zone = "DISCOUNT"
        else:
            zone = "EQUILIBRIUM"

        return {
            "zone": zone,
            "equilibrium": round(equilibrium, 2),
            "price": round(price, 2)
        }
