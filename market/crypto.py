from data.market_data import get_klines

def get_data(symbol="BTCUSDT"):
    candles = get_klines(symbol=symbol, limit=300)

    latest = candles[-1]

    return {
        "market": "CRYPTO",
        "symbol": symbol,
        "price": latest["close"],
        "high": latest["high"],
        "low": latest["low"],
        "volume": latest["volume"],
        "candles": candles,
    }

# ==========================================
# Legacy Compatibility Functions
# ==========================================

def get_crypto(symbol="BTCUSDT"):
    return get_data(symbol)
