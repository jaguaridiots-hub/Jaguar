"""
Jaguar Quant X Enterprise
Canonical Binance Market Data Provider

Provides normalized Binance kline candles.

Canonical candle contract:

{
    "time": int,
    "close_time": int,
    "open": float,
    "high": float,
    "low": float,
    "close": float,
    "volume": float,
}

IMPORTANT:
- Candle identity is preserved.
- Open time is the canonical candle ID.
- No network request is executed at import time.
"""

import requests


BASE = "https://api.binance.com/api/v3/klines"

SYMBOL = "BTCUSDT"

INTERVAL = "15m"


def get_klines(
    symbol=SYMBOL,
    interval=INTERVAL,
    limit=300,
):

    url = (
        f"{BASE}"
        f"?symbol={symbol}"
        f"&interval={interval}"
        f"&limit={limit}"
    )

    response = requests.get(
        url,
        timeout=10,
    )

    response.raise_for_status()

    klines = response.json()

    candles = []

    for kline in klines:

        candles.append(
            {
                "time": int(
                    kline[0]
                ),
                "close_time": int(
                    kline[6]
                ),
                "open": float(
                    kline[1]
                ),
                "high": float(
                    kline[2]
                ),
                "low": float(
                    kline[3]
                ),
                "close": float(
                    kline[4]
                ),
                "volume": float(
                    kline[5]
                ),
            }
        )

    return candles
