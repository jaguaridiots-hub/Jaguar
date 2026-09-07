class MarketRegime:

    @staticmethod
    def detect(ind):

        adx = ind["adx"]["value"]
        atr = ind["atr"]["value"]
        ema20 = ind["ema"]["ema20"]
        ema50 = ind["ema"]["ema50"]
        ema100 = ind["ema"]["ema100"]

        if adx > 30:
            if ema20 > ema50 > ema100:
                return {
                    "regime": "TRENDING_BULLISH"
                }

            elif ema20 < ema50 < ema100:
                return {
                    "regime": "TRENDING_BEARISH"
                }

        if atr > 250:
            return {
                "regime": "HIGH_VOLATILITY"
            }

        if adx < 20:
            return {
                "regime": "RANGING"
            }

        return {
            "regime": "NEUTRAL"
        }
