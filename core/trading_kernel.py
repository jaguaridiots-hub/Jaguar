from market.provider import MarketProvider


class TradingKernel:

    def __init__(self, symbol):
        self.symbol = symbol

    def load(self, interval="15m", limit=500):

        candles = MarketProvider.load(
            self.symbol,
            interval,
            limit
        )

        return {
            "symbol": self.symbol,
            "interval": interval,
            "candles": candles
        }
