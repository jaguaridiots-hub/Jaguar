class Liquidity:

    @staticmethod
    def detect(candles):

        if len(candles) < 20:
            return {
                "found": False,
                "type": "NONE",
                "level": None
            }

        recent = candles[-20:-1]
        last = candles[-1]

        highest = max(c["high"] for c in recent)
        lowest = min(c["low"] for c in recent)

        # Buy-side liquidity sweep
        if last["high"] > highest and last["close"] < highest:
            return {
                "found": True,
                "type": "BUY_SIDE_SWEEP",
                "level": round(highest, 2)
            }

        # Sell-side liquidity sweep
        if last["low"] < lowest and last["close"] > lowest:
            return {
                "found": True,
                "type": "SELL_SIDE_SWEEP",
                "level": round(lowest, 2)
            }

        return {
            "found": False,
            "type": "NONE",
            "level": None
        }
