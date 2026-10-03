"""
Jaguar Quant X
Cache Provider
"""

class CacheProvider:
    name = "CACHE"

    def load(self, symbol, interval, limit):
        raise NotImplementedError(
            "CacheProvider not implemented yet"
        )
