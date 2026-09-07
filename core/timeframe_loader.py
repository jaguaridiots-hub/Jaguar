class TimeframeLoader:

    @staticmethod
    def load(state):

        markets = getattr(state, "market", {}) or {}

        return {
            "15m": markets.get("15m", {"candles": [], "score": 0}),
            "1h":  markets.get("1h",  {"candles": [], "score": 0}),
            "4h":  markets.get("4h",  {"candles": [], "score": 0}),
            "1d":  markets.get("1d",  {"candles": [], "score": 0}),
        }
