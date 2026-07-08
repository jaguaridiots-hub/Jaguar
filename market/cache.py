class MarketCache:

    _cache = {}

    @classmethod
    def get(cls, symbol, interval):
        return cls._cache.get((symbol, interval))

    @classmethod
    def set(cls, symbol, interval, candles):
        cls._cache[(symbol, interval)] = candles
