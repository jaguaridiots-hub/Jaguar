"""
Jaguar Quant X Enterprise

Market Provider Gateway
Version: 1.0

Purpose:
Provide the stable market-data loading facade used by
Jaguar runtime consumers.

Current production provider:
- Binance Spot REST API through the canonical
  data.market_data candle provider.

Provider expansion:
- NSE / BSE / MCX routing will be introduced through
  dedicated API-native providers.
- All providers must return the canonical Jaguar candle
  contract before data reaches analytical engines.

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

Runtime constraints:
- Termux compatible.
- No pandas dependency.
- No yfinance dependency.
- No network request at module import time.
"""

from data.market_data import get_klines


class MarketProvider:
    """
    Stable market-data provider facade.

    The public load() interface is preserved for existing
    TradingKernel consumers.
    """

    @staticmethod
    def load(
        symbol,
        interval="15m",
        limit=500,
    ):
        """
        Load canonical candles for the requested symbol.

        Current routing:
            Binance Spot API

        Future routing:
            Provider registry / exchange-aware gateway.
        """

        return get_klines(
            symbol=symbol,
            interval=interval,
            limit=limit,
        )
