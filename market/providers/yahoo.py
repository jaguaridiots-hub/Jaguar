"""
Jaguar Quant X
Yahoo Provider
"""

class YahooProvider:
    name = "YAHOO"

    def load(self, symbol, interval, limit):
        raise NotImplementedError(
            "YahooProvider not implemented yet"
        )
