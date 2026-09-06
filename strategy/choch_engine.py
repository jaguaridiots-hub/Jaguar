class CHoCHEngine:

    @staticmethod
    def analyze(candles, swing):
        """
        Detect CHoCH from canonical SwingEngine structure.

        CHoCH is a structural transition, not a
        candle-to-candle high/low comparison.
        """

        if not swing:
            return {
                "signal": "SIDEWAYS",
                "reason": "No canonical swing structure available",
            }

        trend = swing.get("trend", "UNKNOWN")
        swings = swing.get("swings", []) or []

        if len(swings) < 2:
            return {
                "signal": "SIDEWAYS",
                "reason": "Insufficient canonical swings",
            }

        last_close = candles[-1]["close"]

        previous_swing_high = swing.get("previous_swing_high")
        previous_swing_low = swing.get("previous_swing_low")

        if trend == "DOWNTREND":
            if (
                previous_swing_high
                and last_close > previous_swing_high["price"]
            ):
                return {
                    "signal": "BULLISH",
                    "reason": "Close above canonical bearish structure high",
                    "level": previous_swing_high,
                }

            return {
                "signal": "SIDEWAYS",
                "reason": "Bearish structure intact",
            }

        if trend == "UPTREND":
            if (
                previous_swing_low
                and last_close < previous_swing_low["price"]
            ):
                return {
                    "signal": "BEARISH",
                    "reason": "Close below canonical bullish structure low",
                    "level": previous_swing_low,
                }

            return {
                "signal": "SIDEWAYS",
                "reason": "Bullish structure intact",
            }

        return {
            "signal": "SIDEWAYS",
            "reason": f"No directional CHoCH in {trend} structure",
        }
