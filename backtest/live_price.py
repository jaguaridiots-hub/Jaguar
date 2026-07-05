import requests

def get_price(symbol):

    try:

        if symbol == "XAUUSD":
            print("Gold live price not supported yet.")
            return None

        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"

        data = requests.get(url, timeout=5).json()

        return float(data["price"])

    except Exception as e:
        print("Live Price Error:", e)
        return None
