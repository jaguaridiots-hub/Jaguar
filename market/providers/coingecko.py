"""
Jaguar Quant X
CoinGecko Provider
"""

import requests


class CoinGeckoProvider:

    name = "COINGECKO"

    def load(self, symbol, interval, limit):
        raise NotImplementedError(
            "CoinGecko provider not implemented yet."
        )
