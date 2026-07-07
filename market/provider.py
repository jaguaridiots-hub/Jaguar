from market.adapter import MarketAdapter


def get_data(symbol):
    return MarketAdapter.load(symbol)


def get_market(symbol):
    return MarketAdapter.get_market(symbol)


if __name__ == "__main__":
    symbols = [
        "BTCUSDT",
        "ETHUSDT",
        "RELIANCE.NS",
        "SBIN.BO",
        "EURUSD=X",
        "AAPL",
        "GOLD"
    ]

    for s in symbols:
        print("=" * 40)
        print("Symbol :", s)
        print("Market :", get_market(s))
        print("Data   :", get_data(s))
