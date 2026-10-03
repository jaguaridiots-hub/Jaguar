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

import math
import time
from datetime import datetime, time as dt_time, timedelta, timezone

from core.market_detector import MarketDetector
from market.adapter import MarketAdapter
from market.provider import MarketProviderError
from market.data_quality import validate_candle_series


class LiveMarketLoaderError(RuntimeError):
    """
    Raised when canonical live market hydration cannot be completed.
    """


CANDLE_FRESHNESS_LATE_TOLERANCE_MS = 30_000

_NSE_TIMEZONE = timezone(timedelta(hours=5, minutes=30))
_NSE_SESSION_OPEN = dt_time(9, 15)
_NSE_SESSION_CLOSE = dt_time(15, 30)


def _nse_session_is_closed(now_ms):
    current = datetime.fromtimestamp(
        int(now_ms) / 1000,
        tz=_NSE_TIMEZONE,
    )

    if current.weekday() >= 5:
        return True

    current_time = current.timetz().replace(tzinfo=None)

    return not (
        _NSE_SESSION_OPEN
        <= current_time
        <= _NSE_SESSION_CLOSE
    )


def _validate_candle_temporal_freshness(
    candle,
    *,
    now_ms=None,
    market_identity=None,
):
    """
    Validate canonical candle timestamps and reject materially stale data.

    The latest Binance candle may still be forming, so freshness is defined
    against its close_time plus a bounded provider/network lateness allowance.
    """
    if not isinstance(candle, dict):
        raise LiveMarketLoaderError(
            "Latest canonical candle must be a dictionary"
        )

    try:
        candle_time = int(candle["time"])
        close_time = int(candle["close_time"])
    except (KeyError, TypeError, ValueError) as exc:
        raise LiveMarketLoaderError(
            "Latest canonical candle timestamps are invalid"
        ) from exc

    if candle_time < 0 or close_time < 0:
        raise LiveMarketLoaderError(
            "Latest canonical candle timestamps must be non-negative"
        )

    if close_time <= candle_time:
        raise LiveMarketLoaderError(
            "Latest canonical candle close_time must be greater than time"
        )

    current_ms = (
        int(float(now_ms))
        if now_ms is not None
        else int(time.time() * 1000)
    )

    if current_ms < candle_time:
        raise LiveMarketLoaderError(
            "Latest canonical candle is future-dated"
        )

    if current_ms > close_time + CANDLE_FRESHNESS_LATE_TOLERANCE_MS:
        if (
            str(market_identity or "").upper() == "NSE"
            and _nse_session_is_closed(current_ms)
        ):
            return {
                "candle_time": candle_time,
                "candle_close_time": close_time,
                "freshness": "SESSION_CLOSED",
            }

        raise LiveMarketLoaderError(
            "Latest canonical candle is stale"
        )

    return {
        "candle_time": candle_time,
        "candle_close_time": close_time,
        "freshness": "CURRENT",
    }


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

    candles = _validate_candles(
        candles
    )

    data_quality = validate_candle_series(
        candles,
        interval=normalized_interval,
        market_identity=market,
    )

    if not data_quality["integrity_ok"]:
        raise LiveMarketLoaderError(
            "Canonical market data integrity failed: "
            f"{data_quality.get('reason') or 'unknown reason'}"
        )

    return candles


def load_market_with_identity(
    symbol,
    interval="15m",
    limit=300,
):
    """
    Load canonical live market data together with execution identity.

    Existing load_market() remains candle-only.
    Identity-aware loading is currently defined for MCX.
    """

    normalized_symbol = _normalize_symbol(symbol)

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

    if market != "MCX":
        candles = load_market(
            normalized_symbol,
            normalized_interval,
            normalized_limit,
        )

        data_quality = validate_candle_series(
            candles,
            interval=normalized_interval,
            market_identity=market,
        )

        return {
            "candles": _validate_candles(candles),
            "instrument_token": None,
            "data_quality": data_quality,
        }

    try:
        result = MarketAdapter.load_with_identity(
            normalized_symbol,
            normalized_interval,
            normalized_limit,
            intraday=True,
        )
    except (MarketProviderError, ValueError) as exc:
        raise LiveMarketLoaderError(
            "Canonical live market identity load failed for "
            f"{normalized_symbol!r}"
        ) from exc

    if not isinstance(result, dict):
        raise LiveMarketLoaderError(
            "Identity-aware market provider result must be a dictionary"
        )

    candles = result.get("candles")

    instrument_token = str(
        result.get("instrument_key", "") or ""
    ).strip()

    if not instrument_token:
        raise LiveMarketLoaderError(
            "Canonical live market identity is unavailable"
        )

    candles = _validate_candles(candles)

    data_quality = validate_candle_series(
        candles,
        interval=normalized_interval,
        market_identity=market,
    )

    if not data_quality["integrity_ok"]:
        raise LiveMarketLoaderError(
            "Canonical market data integrity failed: "
            f"{data_quality.get('reason') or 'unknown reason'}"
        )

    return {
        "candles": candles,
        "instrument_token": instrument_token,
        "data_quality": data_quality,
    }


def update_state(
    state,
    symbol=None,
    limit=300,
    *,
    now_ms=None,
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

    load_result = load_market_with_identity(
        normalized_symbol,
        interval,
        normalized_limit,
    )

    if not isinstance(load_result, dict):
        raise LiveMarketLoaderError(
            "Canonical live market load result is invalid"
        )

    candles = load_result.get("candles")
    instrument_token = str(
        load_result.get("instrument_token", "") or ""
    ).strip()

    market_identity = MarketDetector.detect(
        normalized_symbol
    )

    data_quality = load_result.get("data_quality")

    if not isinstance(data_quality, dict):
        data_quality = validate_candle_series(
            candles,
            interval=interval,
            market_identity=market_identity,
        )

    if not data_quality.get("integrity_ok", False):
        raise LiveMarketLoaderError(
            "Canonical market data integrity failed before hydration: "
            f"{data_quality.get('reason') or 'unknown reason'}"
        )

    latest = candles[-1]
    market_identity = MarketDetector.detect(symbol)

    freshness = _validate_candle_temporal_freshness(
        latest,
        now_ms=now_ms,
        market_identity=market_identity,
    )

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

    # ==================================================
    # CANONICAL DATA-QUALITY / EXECUTION CONTRACT
    # ==================================================
    # Full candle-series integrity is authoritative.
    # Latest-candle freshness remains a separate temporal gate.
    # ==================================================

    integrity_ok = bool(
        data_quality.get(
            "integrity_ok",
            False,
        )
    )

    provider_source = {
        "CRYPTO": "BINANCE",
        "MCX": "UPSTOX",
        "NSE": "YAHOO_NSE",
    }.get(
        market_identity,
        "UNKNOWN",
    )

    provider_known = provider_source != "UNKNOWN"

    execution_authorized_sources = {
        "BINANCE",
        "UPSTOX",
    }

    temporal_ok = freshness["freshness"] in {
        "CURRENT",
        "SESSION_CLOSED",
    }

    execution_temporal_ok = freshness["freshness"] == "CURRENT"

    state.market_metadata = {
        "source": provider_source,
        "synthetic": not provider_known,
        "live_data_valid": (
            integrity_ok
            and provider_known
            and temporal_ok
        ),
        "execution_allowed": (
            integrity_ok
            and provider_known
            and execution_temporal_ok
            and provider_source in execution_authorized_sources
        ),
        "instrument_token": instrument_token,
        "candle_time": freshness["candle_time"],
        "candle_close_time": freshness["candle_close_time"],
        "freshness": freshness["freshness"],
        "data_quality": data_quality,
    }

    return state
