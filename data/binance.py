import requests

print("====== Binance Live Data ======")

symbol = "BTCUSDT"
interval = "15m"
limit = 2

url = (
    f"https://api.binance.com/api/v3/klines"
    f"?symbol={symbol}&interval={interval}&limit={limit}"
)

try:
    data = requests.get(url, timeout=10).json()

    last = data[-1]

    print("Exchange :", "Binance")
    print("Symbol   :", symbol)
    print("Interval :", interval)
    print()

    print("Open   :", last[1])
    print("High   :", last[2])
    print("Low    :", last[3])
    print("Close  :", last[4])
    print("Volume :", last[5])

except Exception as e:
    print("Connection Failed")
    print(e)
