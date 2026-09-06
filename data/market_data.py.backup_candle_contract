import requests

BASE = "https://api.binance.com/api/v3/klines"

SYMBOL = "BTCUSDT"
INTERVAL = "15m"


def get_klines(symbol=SYMBOL, interval=INTERVAL, limit=300):

    url = (
        f"{BASE}?symbol={symbol}"
        f"&interval={interval}"
        f"&limit={limit}"
    )

    response = requests.get(url, timeout=10)
    response.raise_for_status()

    klines = response.json()

    candles = []

    for k in klines:
        candles.append({
            "open": float(k[1]),
            "high": float(k[2]),
            "low": float(k[3]),
            "close": float(k[4]),
            "volume": float(k[5]),
        })

    return candles


candles = get_klines()
