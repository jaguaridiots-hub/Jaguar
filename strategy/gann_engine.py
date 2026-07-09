import math

class GannEngine:

    def run(self, state, bus):

        bus.publish("GANN_ANALYSIS")

        candles = state.market_current["candles"]

        price = float(candles[-1]["close"])

        root = math.sqrt(price)

        angles = {
            "45": round((root + 0.125) ** 2, 2),
            "90": round((root + 0.25) ** 2, 2),
            "180": round((root + 0.50) ** 2, 2),
            "270": round((root + 0.75) ** 2, 2),
            "360": round((root + 1.00) ** 2, 2)
        }

        support = round((root - 0.25) ** 2, 2)
        resistance = round((root + 0.25) ** 2, 2)

        score = 0
        signal = "NEUTRAL"
        reasons = []

        if price > resistance:
            signal = "BULLISH"
            score = 20
            reasons.append("Price above Gann Resistance")

        elif price < support:
            signal = "BEARISH"
            score = -20
            reasons.append("Price below Gann Support")

        else:
            reasons.append("Inside Gann Range")

        nearest = min(
            [support, resistance] + list(angles.values()),
            key=lambda x: abs(price - x)
        )

        state.gann = {
            "signal": signal,
            "score": score,
            "price": round(price, 2),
            "support": support,
            "resistance": resistance,
            "nearest_level": round(nearest, 2),
            "angles": angles,
            "reasons": reasons,
        }

        bus.publish("GANN_READY")

        return state
