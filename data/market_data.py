from binance.client import Client

client = Client()

SYMBOL = "BTCUSDT"
INTERVAL = Client.KLINE_INTERVAL_15MINUTE

klines = client.get_klines(
    symbol=SYMBOL,
    interval=INTERVAL,
    limit=300
)

candles = []

for k in klines:
    candles.append({
        "open": float(k[1]),
        "high": float(k[2]),
        "low": float(k[3]),
        "close": float(k[4]),
        "volume": float(k[5]),
    })

def get_klines(symbol=SYMBOL, interval=INTERVAL, limit=300):
    klines = client.get_klines(
        symbol=symbol,
        interval=interval,
        limit=limit
    )

    data = []

    for k in klines:
        data.append({
            "open": float(k[1]),
            "high": float(k[2]),
            "low": float(k[3]),
            "close": float(k[4]),
            "volume": float(k[5]),
        })

    return data
