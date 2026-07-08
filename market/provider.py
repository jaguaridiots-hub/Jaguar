from market.binance_live import BinanceLive

class MarketProvider:

    @staticmethod
    def load(symbol, interval="15m", limit=500):
        return BinanceLive.load(symbol, interval, limit)
