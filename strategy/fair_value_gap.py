class FairValueGap:

    @staticmethod
    def detect(candles):

        if len(candles) < 3:
            return {
                "found": False,
                "type": "NONE",
                "top": None,
                "bottom": None,
                "score": 0,
                "reasons": []
            }

        c1 = candles[-3]
        c2 = candles[-2]
        c3 = candles[-1]

        # Bullish FVG
        if c1["high"] < c3["low"]:
            return {
                "found": True,
                "type": "BULLISH",
                "top": round(c3["low"], 2),
                "bottom": round(c1["high"], 2),
                "score": 20,
                "reasons": ["Bullish Fair Value Gap"]
            }

        # Bearish FVG
        elif c1["low"] > c3["high"]:
            return {
                "found": True,
                "type": "BEARISH",
                "top": round(c1["low"], 2),
                "bottom": round(c3["high"], 2),
                "score": -20,
                "reasons": ["Bearish Fair Value Gap"]
            }

        return {
            "found": False,
            "type": "NONE",
            "top": None,
            "bottom": None,
            "score": 0,
            "reasons": []
        }
