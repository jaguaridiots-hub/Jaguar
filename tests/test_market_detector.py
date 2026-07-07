from core.market_detector import MarketDetector

symbols = [
    "BTCUSDT",
    "ETHUSDT",
    "RELIANCE.NS",
    "TCS.NS",
    "SBIN.BO",
    "XAUUSD",
    "EURUSD",
    "AAPL",
    "TSLA",
    "GOLD"
]

for s in symbols:
    print(s, "->", MarketDetector.detect(s))
