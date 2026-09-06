import requests

symbol = "APPL"
url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

params = {
    "interval": "15m",
    "range": "1d"
}

resp = requests.get(url, headers=headers, params=params)

print("Status:", resp.status_code)

if resp.status_code == 200:
    data = resp.json()
    price = data["chart"]["result"][0]["meta"]["regularMarketPrice"]
    print(f"💰 Gold price: ${price}")
else:
    print("❌ Failed. Response:", resp.text[:200])
