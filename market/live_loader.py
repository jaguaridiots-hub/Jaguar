"""
Jaguar Quant X Enterprise
Canonical Live Market Loader

Purpose:
Provide the live runtime hydration boundary between the canonical
MarketProvider candle gateway and Jaguar MarketState.

Pipeline:
live runtime intent
    -> deterministic market identity
    -> canonical MarketProvider routing
    -> canonical Jaguar candles
    -> latest candle hydration
    -> existing MarketState object

Current live capabilities:
- CRYPTO -> canonical Binance provider
- MCX    -> canonical Upstox provider with explicit intraday intent

Unsupported provider capabilities fail closed through MarketProvider.

State contract:
- preserve the existing state object
- preserve the existing state.market dictionary identity
- hydrate legacy scalar market fields
- synchronize canonical market context
- preserve the complete canonical candle dataset

Runtime constraints:
- Termux compatible
- no pandas dependency
- no yfinance dependency
- no network request at module import time
"""

from core.market_detector import MarketDetector
from market.adapter import MarketAdapter
from market.provider import MarketProviderError


class LiveMarketLoaderError(RuntimeError):
    """
    Raised when canonical live market hydration cannot be completed.
    """


def _normalize_symbol(symbol):
    """
    Normalize and validate the requested live market symbol.
    """

    if symbol is None:
        raise LiveMarketLoaderError(
            "Market symbol is required to update state"
        )

    normalized = str(symbol).strip().upper()

    if not normalized:
        raise LiveMarketLoaderError(
            "Market symbol is required to update state"
        )

    return normalized


def _normalize_interval(state):
    """
    Resolve the canonical live interval from MarketState.

    MarketState uses timeframe while the provider gateway uses interval.
    """

    interval = getattr(
        state,
        "timeframe",
        None,
    )

    if interval is None:
        raise LiveMarketLoaderError(
            "Market timeframe is required to update state"
        )

    normalized = str(interval).strip()

    if not normalized:
        raise LiveMarketLoaderError(
            "Market timeframe is required to update state"
        )

    return normalized


def _normalize_limit(limit):
    """
    Validate the requested canonical live candle limit.
    """

    if isinstance(limit, bool):
        raise LiveMarketLoaderError(
            "Live candle limit must be a positive integer"
        )

    try:
        normalized = int(limit)

    except (TypeError, ValueError) as exc:

        raise LiveMarketLoaderError(
            f"Invalid live candle limit: {limit!r}"
        ) from exc

    if normalized <= 0:
        raise LiveMarketLoaderError(
            "Live candle limit must be positive"
        )

    return normalized


def _validate_candles(candles):
    """
    Validate the minimum canonical candle surface required for
    live MarketState hydration.
    """

    if not isinstance(candles, list):
        raise LiveMarketLoaderError(
            "Canonical market provider must return a candle list"
        )

    if not candles:
        raise LiveMarketLoaderError(
            "Canonical market provider returned no candles"
        )

    required_fields = (
        "time",
        "close_time",
        "open",
        "high",
        "low",
        "close",
        "volume",
    )

    for index, candle in enumerate(candles):

        if not isinstance(candle, dict):
            raise LiveMarketLoaderError(
                "Canonical candle must be a dictionary "
                f"at index {index}"
            )

        actual_fields = tuple(
            candle.keys()
        )

        if actual_fields != required_fields:
            raise LiveMarketLoaderError(
                "Canonical candle field contract mismatch "
                f"at index {index}: {actual_fields!r}"
            )

    return candles


def load_market(
    symbol,
    interval="15m",
    limit=300,
):
    """
    Load canonical candles for a live runtime refresh.

    LiveLoader explicitly declares intraday intent for MCX.
    CRYPTO preserves the canonical three-argument provider route.

    Unsupported provider capabilities fail closed through
    MarketProvider.
    """

    normalized_symbol = _normalize_symbol(
        symbol
    )

    normalized_interval = str(
        interval
    ).strip()

    if not normalized_interval:
        raise LiveMarketLoaderError(
            "Market interval is required for live loading"
        )

    normalized_limit = _normalize_limit(
        limit
    )

    market = MarketDetector.detect(
        normalized_symbol
    )

    try:

        if market == "MCX":

            candles = MarketAdapter.load(
                normalized_symbol,
                normalized_interval,
                normalized_limit,
                intraday=True,
            )

        else:

            candles = MarketAdapter.load(
                normalized_symbol,
                normalized_interval,
                normalized_limit,
            )

    except MarketProviderError as exc:

        raise LiveMarketLoaderError(
            "Canonical live market load failed for "
            f"{normalized_symbol!r}"
        ) from exc

    return _validate_candles(
        candles
    )


def update_state(
    state,
    symbol=None,
    limit=300,
):
    """
    Hydrate the existing Jaguar MarketState from canonical live candles.

    The state object identity is preserved.

    The state.market dictionary identity is also preserved so analytical
    context written by enterprise engines is not discarded.
    """

    if state is None:
        raise LiveMarketLoaderError(
            "Market state is required for live hydration"
        )

    if symbol is None:
        symbol = getattr(
            state,
            "symbol",
            None,
        )

    normalized_symbol = _normalize_symbol(
        symbol
    )

    interval = _normalize_interval(
        state
    )

    normalized_limit = _normalize_limit(
        limit
    )

    candles = load_market(
        normalized_symbol,
        interval,
        normalized_limit,
    )

    latest = candles[-1]

    try:

        price = float(
            latest["close"]
        )

        high = float(
            latest["high"]
        )

        low = float(
            latest["low"]
        )

        volume = float(
            latest["volume"]
        )

    except (
        KeyError,
        TypeError,
        ValueError,
    ) as exc:

        raise LiveMarketLoaderError(
            "Latest canonical candle cannot hydrate MarketState"
        ) from exc

    market = getattr(
        state,
        "market",
        None,
    )

    if not isinstance(
        market,
        dict,
    ):

        raise LiveMarketLoaderError(
            "MarketState market context must be a dictionary"
        )

    market_identity = MarketDetector.detect(
        normalized_symbol
    )

    state.symbol = normalized_symbol
    state.price = price
    state.high = high
    state.low = low
    state.volume = volume

    market["market"] = market_identity
    market["symbol"] = normalized_symbol
    market["price"] = price
    market["high"] = high
    market["low"] = low
    market["volume"] = volume
    market["candles"] = candles

    return state
