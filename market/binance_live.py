import requests


class BinanceLive:

    BASE = "https://api.binance.com"

    @staticmethod
    def load(symbol="BTCUSDT", interval="15m", limit=500):

        url = (
            f"{BinanceLive.BASE}/api/v3/klines"
            f"?symbol={symbol}"
            f"&interval={interval}"
            f"&limit={limit}"
        )

        response = requests.get(url, timeout=10)

        if response.status_code != 200:
            raise Exception(response.text)

        raw = response.json()

        candles = []

        for k in raw:
            candles.append({
                "time": int(k[0]),
                "open": float(k[1]),
                "high": float(k[2]),
                "low": float(k[3]),
                "close": float(k[4]),
                "volume": float(k[5])
            })

        return candles
