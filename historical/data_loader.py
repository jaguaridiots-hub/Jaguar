import requests

BASE_URL = "https://api.binance.com/api/v3/klines"

def load_data(symbol="BTCUSDT", interval="15m", limit=1000):

    url = (
        f"{BASE_URL}?symbol={symbol}"
        f"&interval={interval}"
        f"&limit={limit}"
    )

    response = requests.get(url, timeout=10)

    if response.status_code != 200:
        print("Unable to fetch historical candles.")
        return []

    data = response.json()

    candles = []

    for candle in data:
        candles.append({
            "time": candle[0],
            "open": float(candle[1]),
            "high": float(candle[2]),
            "low": float(candle[3]),
            "close": float(candle[4]),
            "volume": float(candle[5]),
        })

    return candles


if __name__ == "__main__":

    candles = load_data()

    print("\n====== JAGUAR HISTORICAL DATA ======\n")
    print("Candles Loaded :", len(candles))

    if candles:
        print("First Close :", candles[0]["close"])
        print("Last Close  :", candles[-1]["close"])
