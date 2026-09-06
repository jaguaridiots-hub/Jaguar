from market.adapter import MarketAdapter

symbols = [
    "BTCUSDT",
    "RELIANCE.NS",
    "SBIN.BO",
    "EURUSD",
    "AAPL",
    "GOLD"
]

for symbol in symbols:
    print(MarketAdapter.load(symbol))
