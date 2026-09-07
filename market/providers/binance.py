from data.market_data import get_klines

class BinanceProvider:
    name = "BINANCE"

    def load(self, symbol, interval, limit):
        return get_klines(
            symbol=symbol,
            interval=interval,
            limit=limit,
        )
