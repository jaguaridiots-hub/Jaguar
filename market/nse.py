import yfinance as yf

def get_data(symbol):
    t = yf.Ticker(symbol)

    hist = t.history(period="5d", interval="15m")

    return {
        "market": "NSE",
        "symbol": symbol,
        "price": float(hist["Close"].iloc[-1]),
        "high": float(hist["High"].iloc[-1]),
        "low": float(hist["Low"].iloc[-1]),
        "volume": float(hist["Volume"].iloc[-1]),
        "candles": hist.tail(300).to_dict("records")
    }
