from market.provider import get_data

class MarketFeed:

    @staticmethod
    def fetch(symbol):
        data = get_data(symbol)

        return {
            "symbol": symbol,
            "market": data.get("market"),
            "price": data.get("price", 0),
            "high": data.get("high", 0),
            "low": data.get("low", 0),
            "volume": data.get("volume", 0),
            "candles": data.get("candles", [])
        }
