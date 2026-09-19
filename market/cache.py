import time


class MarketCache:
    _cache = {}
    _timestamps = {}
    _clock = staticmethod(time.monotonic)

    @classmethod
    def get(cls, symbol, interval):
        return cls._cache.get((symbol, interval))

    @classmethod
    def set(cls, symbol, interval, candles):
        key = (symbol, interval)
        cls._cache[key] = list(candles)
        cls._timestamps[key] = cls._clock()

    @classmethod
    def get_fresh(cls, symbol, interval, max_age_seconds):
        key = (symbol, interval)

        candles = cls._cache.get(key)
        stored_at = cls._timestamps.get(key)

        if candles is None or stored_at is None:
            return None

        age = cls._clock() - stored_at

        if age < 0 or age > float(max_age_seconds):
            return None

        return list(candles)

    @classmethod
    def clear(cls):
        cls._cache.clear()
        cls._timestamps.clear()
