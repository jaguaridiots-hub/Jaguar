import time

from market.cache import MarketCache


def main():
    MarketCache.clear()

    original_clock = MarketCache._clock
    now = [100.0]

    try:
        MarketCache._clock = staticmethod(lambda: now[0])

        candles = [
            {
                "time": 1700000100000,
                "close_time": 1700001000000,
                "open": 100.0,
                "high": 101.0,
                "low": 99.0,
                "close": 100.5,
                "volume": 1000.0,
            }
        ]

        MarketCache.set("RELIANCE.NS", "15m", candles)

        fresh = MarketCache.get_fresh(
            "RELIANCE.NS",
            "15m",
            10.0,
        )

        assert fresh == candles, "Fresh cache entry was not returned"

        now[0] += 10.001

        expired = MarketCache.get_fresh(
            "RELIANCE.NS",
            "15m",
            10.0,
        )

        assert expired is None, "Expired cache entry was returned"

        print("NSE_PROVIDER_CACHE_TTL_CONTRACT: PASS")

    finally:
        MarketCache._clock = original_clock
        MarketCache.clear()


if __name__ == "__main__":
    main()
