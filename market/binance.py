import requests

BASE = "https://api.binance.com/api/v3/ticker/24hr"

def get_price(symbol="BTCUSDT"):
    r = requests.get(BASE, params={"symbol": symbol}, timeout=10)
    data = r.json()

    return {
        "symbol": data["symbol"],
        "price": float(data["lastPrice"]),
        "high": float(data["highPrice"]),
        "low": float(data["lowPrice"]),
        "volume": float(data["volume"])
    }
