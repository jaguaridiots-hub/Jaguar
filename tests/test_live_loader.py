from market.adapter import MarketAdapter

def load_market(symbol):
    return MarketAdapter.load(symbol)

symbols = [
    "BTCUSDT",
    "ETHUSDT",
    "RELIANCE.NS",
    "SBIN.BO",
    "EURUSD",
    "AAPL",
    "GOLD"
]

for s in symbols:
    print(load_market(s))
