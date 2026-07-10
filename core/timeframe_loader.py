class TimeframeLoader:

    @staticmethod
    def load(state):

        market = getattr(state, "market_current", {})

        candles = market.get("candles", [])

        return {
            "15m": {
                "candles": candles,
                "score": 0
            },
            "1h": {
                "candles": candles,
                "score": 0
            },
            "4h": {
                "candles": candles,
                "score": 0
            },
            "1d": {
                "candles": candles,
                "score": 0
            }
        }
