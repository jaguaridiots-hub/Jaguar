"""
Canonical NSE market-data provider.

Source:
    Yahoo Finance Chart API

Scope:
    NSE equity market data for PAPER/dashboard analysis.

This module does not:
    - place orders
    - access broker execution APIs
    - authorize LIVE execution
    - mutate JaguarState
"""

import json
import math
import urllib.parse
import urllib.request

from market.cache import MarketCache


class NSEProviderError(RuntimeError):
    """Raised when canonical NSE market data cannot be loaded."""


_INTERVAL_CONFIG = {
    "15m": {
        "range": "5d",
        "seconds": 900,
    },
}


class NSEProvider:
    """
    Canonical Yahoo-backed NSE candle provider.
    """

    CACHE_TTL_SECONDS = 10.0

    def __init__(self, opener=None):
        self._opener = opener or urllib.request.urlopen

    @staticmethod
    def _normalize_symbol(symbol):
        if symbol is None:
            raise NSEProviderError("NSE symbol is required")

        normalized = str(symbol).strip().upper()

        if not normalized.endswith(".NS"):
            raise NSEProviderError(
                f"Unsupported NSE symbol: {symbol!r}"
            )

        if normalized == ".NS":
            raise NSEProviderError("NSE symbol is invalid")

        return normalized

    @staticmethod
    def _interval_config(interval):
        normalized = str(interval or "").strip()

        config = _INTERVAL_CONFIG.get(normalized)

        if config is None:
            raise NSEProviderError(
                f"Unsupported NSE interval: {interval!r}"
            )

        return normalized, config

    @staticmethod
    def _validate_value(name, value):
        try:
            numeric = float(value)
        except (TypeError, ValueError) as exc:
            raise NSEProviderError(
                f"NSE candle value is invalid: {name}"
            ) from exc

        if not math.isfinite(numeric):
            raise NSEProviderError(
                f"NSE candle value is non-finite: {name}"
            )

        return numeric

    def _build_url(self, symbol, interval, range_value):
        return (
            "https://query1.finance.yahoo.com/v8/finance/chart/"
            + urllib.parse.quote(symbol, safe="")
            + "?"
            + urllib.parse.urlencode(
                {
                    "interval": interval,
                    "range": range_value,
                }
            )
        )

    def _fetch_payload(self, url):
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/json",
            },
            method="GET",
        )

        try:
            with self._opener(request, timeout=15) as response:
                raw = response.read()
        except Exception as exc:
            raise NSEProviderError(
                "NSE market-data request failed"
            ) from exc

        try:
            return json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise NSEProviderError(
                "NSE market-data response is not valid JSON"
            ) from exc

    def load(self, symbol, interval="15m", limit=300):
        symbol = self._normalize_symbol(symbol)

        interval, interval_config = self._interval_config(interval)

        try:
            normalized_limit = int(limit)
        except (TypeError, ValueError) as exc:
            raise NSEProviderError(
                "NSE candle limit must be an integer"
            ) from exc

        if normalized_limit <= 0:
            raise NSEProviderError(
                "NSE candle limit must be positive"
            )

        cached = MarketCache.get_fresh(
            symbol,
            interval,
            self.CACHE_TTL_SECONDS,
        )

        if cached is not None:
            return cached[-normalized_limit:]

        url = self._build_url(
            symbol,
            interval,
            interval_config["range"],
        )

        payload = self._fetch_payload(url)

        chart = payload.get("chart")
        if not isinstance(chart, dict):
            raise NSEProviderError(
                "NSE response missing chart object"
            )

        if chart.get("error") is not None:
            raise NSEProviderError(
                f"NSE market-data error: {chart['error']}"
            )

        results = chart.get("result")
        if not isinstance(results, list) or not results:
            raise NSEProviderError(
                "NSE response contains no chart result"
            )

        result = results[0]
        timestamps = result.get("timestamp")
        indicators = result.get("indicators")

        if not isinstance(timestamps, list):
            raise NSEProviderError(
                "NSE response contains invalid timestamps"
            )

        if not isinstance(indicators, dict):
            raise NSEProviderError(
                "NSE response contains invalid indicators"
            )

        quotes = indicators.get("quote")
        if not isinstance(quotes, list) or not quotes:
            raise NSEProviderError(
                "NSE response contains no quote data"
            )

        quote = quotes[0]

        if not isinstance(quote, dict):
            raise NSEProviderError(
                "NSE quote payload is invalid"
            )

        required = (
            "open",
            "high",
            "low",
            "close",
            "volume",
        )

        for field in required:
            if not isinstance(quote.get(field), list):
                raise NSEProviderError(
                    f"NSE quote field is invalid: {field}"
                )

        interval_ms = interval_config["seconds"] * 1000

        candles = []

        for index, timestamp in enumerate(timestamps):
            if (
                index >= len(quote["open"])
                or index >= len(quote["high"])
                or index >= len(quote["low"])
                or index >= len(quote["close"])
                or index >= len(quote["volume"])
            ):
                continue

            if timestamp is None:
                continue

            try:
                candle_time = int(timestamp) * 1000
            except (TypeError, ValueError):
                continue

            # Yahoo may append a current quote-like row whose timestamp
            # is not aligned to the requested interval. Do not promote it.
            if candle_time % interval_ms != 0:
                continue

            try:
                open_value = self._validate_value(
                    "open",
                    quote["open"][index],
                )
                high_value = self._validate_value(
                    "high",
                    quote["high"][index],
                )
                low_value = self._validate_value(
                    "low",
                    quote["low"][index],
                )
                close_value = self._validate_value(
                    "close",
                    quote["close"][index],
                )
                volume_value = self._validate_value(
                    "volume",
                    quote["volume"][index],
                )
            except NSEProviderError:
                continue

            if (
                open_value <= 0
                or high_value <= 0
                or low_value <= 0
                or close_value <= 0
                or volume_value <= 0
            ):
                continue

            if high_value < max(open_value, close_value):
                continue

            if low_value > min(open_value, close_value):
                continue

            if high_value <= low_value:
                continue

            candles.append(
                {
                    "time": candle_time,
                    "close_time": candle_time + interval_ms,
                    "open": open_value,
                    "high": high_value,
                    "low": low_value,
                    "close": close_value,
                    "volume": volume_value,
                }
            )

        if not candles:
            raise NSEProviderError(
                f"NSE provider returned no valid {interval} candles"
            )

        MarketCache.set(
            symbol,
            interval,
            candles,
        )

        return candles[-normalized_limit:]
