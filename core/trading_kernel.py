from core.market_feed import MarketFeed


class TradingKernel:

    def __init__(self, symbol):
        self.symbol = symbol
        self.market = None
        self.data = None

    def load(self):
        self.data = MarketFeed.fetch(self.symbol)
        self.market = self.data["market"]

        return self.data

    def info(self):
        return {
            "symbol": self.symbol,
            "market": self.market,
            "price": self.data["price"]
        }
