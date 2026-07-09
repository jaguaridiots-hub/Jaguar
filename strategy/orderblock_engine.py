class OrderBlockEngine:

    def run(self, state, bus):

        bus.publish("ORDERBLOCK_ANALYSIS")

        candles = state.market_current["candles"]

        bullish = None
        bearish = None

        # Scan the last 50 candles
        for i in range(len(candles) - 50, len(candles) - 2):

            c1 = candles[i]
            c2 = candles[i + 1]

            body = abs(c2["close"] - c2["open"])
            rng = c2["high"] - c2["low"]

            if rng == 0:
                continue

            displacement = body / rng

            # Bullish Order Block
            if (
                c1["close"] < c1["open"]
                and c2["close"] > c2["high"]
                and displacement > 0.70
            ):
                bullish = {
                    "high": c1["high"],
                    "low": c1["low"],
                    "index": i
                }

            # Bearish Order Block
            if (
                c1["close"] > c1["open"]
                and c2["close"] < c2["low"]
                and displacement > 0.70
            ):
                bearish = {
                    "high": c1["high"],
                    "low": c1["low"],
                    "index": i
                }

        state.orderblock = {
            "bullish": bullish,
            "bearish": bearish
        }

        bus.publish("ORDERBLOCK_READY")

        return state
