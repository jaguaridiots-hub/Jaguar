# core/asset_registry.py
"""
Centralized asset registry for Jaguar Quant X.
Provides metadata and Yahoo symbol mapping for all supported assets.
"""

ASSET_REGISTRY = {
    # ========================
    # Crypto (Yahoo symbols)
    # ========================
    "BTCUSDT": {
        "symbol": "BTCUSDT",
        "yahoo_symbol": "BTC-USD",
        "exchange": "CCC",
        "asset_class": "crypto",
        "trading_hours": "24/7",
        "timezone": "UTC",
        "tick_size": 0.01,
        "currency": "USD",
    },
    "ETHUSDT": {
        "symbol": "ETHUSDT",
        "yahoo_symbol": "ETH-USD",
        "exchange": "CCC",
        "asset_class": "crypto",
        "trading_hours": "24/7",
        "timezone": "UTC",
        "tick_size": 0.01,
        "currency": "USD",
    },
    "SOLUSDT": {
        "symbol": "SOLUSDT",
        "yahoo_symbol": "SOL-USD",
        "exchange": "CCC",
        "asset_class": "crypto",
        "trading_hours": "24/7",
        "timezone": "UTC",
        "tick_size": 0.001,
        "currency": "USD",
    },

    # ========================
    # Commodities
    # ========================
    "GC=F": {
        "symbol": "GC=F",
        "yahoo_symbol": "GC=F",
        "exchange": "CMX",
        "asset_class": "commodity",
        "trading_hours": "18:00–17:00 (next day) ET",
        "timezone": "America/New_York",
        "tick_size": 0.1,
        "currency": "USD",
    },
    "SI=F": {
        "symbol": "SI=F",
        "yahoo_symbol": "SI=F",
        "exchange": "CMX",
        "asset_class": "commodity",
        "trading_hours": "18:00–17:00 (next day) ET",
        "timezone": "America/New_York",
        "tick_size": 0.005,
        "currency": "USD",
    },

    # ========================
    # US Stocks
    # ========================
    "AAPL": {
        "symbol": "AAPL",
        "yahoo_symbol": "AAPL",
        "exchange": "NASDAQ",
        "asset_class": "stock",
        "trading_hours": "09:30–16:00 ET",
        "timezone": "America/New_York",
        "tick_size": 0.01,
        "currency": "USD",
    },
    "MSFT": {
        "symbol": "MSFT",
        "yahoo_symbol": "MSFT",
        "exchange": "NASDAQ",
        "asset_class": "stock",
        "trading_hours": "09:30–16:00 ET",
        "timezone": "America/New_York",
        "tick_size": 0.01,
        "currency": "USD",
    },
    "NVDA": {
        "symbol": "NVDA",
        "yahoo_symbol": "NVDA",
        "exchange": "NASDAQ",
        "asset_class": "stock",
        "trading_hours": "09:30–16:00 ET",
        "timezone": "America/New_York",
        "tick_size": 0.01,
        "currency": "USD",
    },

    # ========================
    # India Stocks (NSE)
    # ========================
    "RELIANCE.NS": {
        "symbol": "RELIANCE.NS",
        "yahoo_symbol": "RELIANCE.NS",
        "exchange": "NSE",
        "asset_class": "stock",
        "trading_hours": "09:15–15:30 IST",
        "timezone": "Asia/Kolkata",
        "tick_size": 0.05,
        "currency": "INR",
    },
    "TCS.NS": {
        "symbol": "TCS.NS",
        "yahoo_symbol": "TCS.NS",
        "exchange": "NSE",
        "asset_class": "stock",
        "trading_hours": "09:15–15:30 IST",
        "timezone": "Asia/Kolkata",
        "tick_size": 0.05,
        "currency": "INR",
    },
    "HDFCBANK.NS": {
        "symbol": "HDFCBANK.NS",
        "yahoo_symbol": "HDFCBANK.NS",
        "exchange": "NSE",
        "asset_class": "stock",
        "trading_hours": "09:15–15:30 IST",
        "timezone": "Asia/Kolkata",
        "tick_size": 0.05,
        "currency": "INR",
    },

    # ========================
    # Indices
    # ========================
    "^GSPC": {
        "symbol": "^GSPC",
        "yahoo_symbol": "^GSPC",
        "exchange": "SPX",
        "asset_class": "index",
        "trading_hours": "09:30–16:00 ET",
        "timezone": "America/New_York",
        "tick_size": 0.01,
        "currency": "USD",
    },
    "^IXIC": {
        "symbol": "^IXIC",
        "yahoo_symbol": "^IXIC",
        "exchange": "NASDAQ",
        "asset_class": "index",
        "trading_hours": "09:30–16:00 ET",
        "timezone": "America/New_York",
        "tick_size": 0.01,
        "currency": "USD",
    },
    "^NSEI": {
        "symbol": "^NSEI",
        "yahoo_symbol": "^NSEI",
        "exchange": "NSE",
        "asset_class": "index",
        "trading_hours": "09:15–15:30 IST",
        "timezone": "Asia/Kolkata",
        "tick_size": 0.05,
        "currency": "INR",
    },

    # ========================
    # Forex
    # ========================
    "EURUSD=X": {
        "symbol": "EURUSD=X",
        "yahoo_symbol": "EURUSD=X",
        "exchange": "FOREX",
        "asset_class": "forex",
        "trading_hours": "24/7",
        "timezone": "UTC",
        "tick_size": 0.00001,
        "currency": "USD",
    },
    "GBPUSD=X": {
        "symbol": "GBPUSD=X",
        "yahoo_symbol": "GBPUSD=X",
        "exchange": "FOREX",
        "asset_class": "forex",
        "trading_hours": "24/7",
        "timezone": "UTC",
        "tick_size": 0.00001,
        "currency": "USD",
    },
}


def get_asset_metadata(symbol):
    """Return metadata for a given symbol, or None if not found."""
    return ASSET_REGISTRY.get(symbol)


def get_yahoo_symbol(symbol):
    """Return the Yahoo Finance symbol for a given asset symbol."""
    meta = get_asset_metadata(symbol)
    if meta:
        return meta.get("yahoo_symbol")
    return symbol  # fallback to the symbol itself


def get_asset_class(symbol):
    """Return the asset class (crypto, stock, commodity, etc.)."""
    meta = get_asset_metadata(symbol)
    return meta.get("asset_class") if meta else "unknown"


def get_currency(symbol):
    """Return the quote currency for the asset."""
    meta = get_asset_metadata(symbol)
    return meta.get("currency") if meta else "USD"
