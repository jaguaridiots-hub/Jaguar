import requests

symbols = ["GC=F", "AAPL", "BTC-USD", "EURUSD=X"]

for sym in symbols:
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}"
    headers = {"User-Agent": "Mozilla/5.0"}
    params = {"interval": "15m", "range": "1d"}
    resp = requests.get(url, headers=headers, params=params, timeout=10)
    
    print(f"{sym}: Status {resp.status_code}")
    if resp.status_code == 200:
        try:
            data = resp.json()
            price = data["chart"]["result"][0]["meta"]["regularMarketPrice"]
            print(f"  ✅ Price: {price}")
        except:
            print("  ❌ Invalid JSON")
    else:
        print(f"  ❌ Failed: {resp.text[:100]}")
    print()
