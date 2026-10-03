"""
Jaguar Quant X
Provider Manager

Provider priority:

1. Binance
2. Yahoo
3. CoinGecko
4. Cache
"""

from market.providers.binance import BinanceProvider
from market.providers.yahoo import YahooProvider
from market.providers.coingecko import CoinGeckoProvider
from market.providers.cache import CacheProvider


class ProviderManager:

    PROVIDERS = [
        BinanceProvider(),
        YahooProvider(),
        CoinGeckoProvider(),
        CacheProvider(),
    ]

    @classmethod
    def load(cls, symbol, interval, limit):

        last_error = None

        for provider in cls.PROVIDERS:

            try:

                data = provider.load(
                    symbol,
                    interval,
                    limit,
                )

                if data:
                    print(f"[Provider] {provider.name} SUCCESS")
                    return data

            except Exception as e:

                print(f"[Provider] {provider.name} FAILED : {e}")
                last_error = e

        if last_error:
            raise last_error

        raise RuntimeError("No provider returned data")
