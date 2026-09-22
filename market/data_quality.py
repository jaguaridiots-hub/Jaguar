"""
Jaguar Quant X Enterprise
Canonical Market Data Quality Contract.

This module is the single data-quality authority for canonical
live candle series before MarketState execution eligibility.

Design:
    provider candles
        -> schema / numeric / OHLCV validation
        -> timestamp ordering / duplicates
        -> requested interval consistency
        -> gap detection
        -> integrity result

Gap policy:
    CRYPTO = continuous market; unexpected gaps fail integrity.
    NSE/MCX = session-based markets; gaps remain explicitly
              visible as diagnostics and do not alone invalidate
              the whole series.
"""

from __future__ import annotations

from collections import Counter
import math


EXPECTED_FIELDS = (
    "time",
    "close_time",
    "open",
    "high",
    "low",
    "close",
    "volume",
)


INTERVAL_MS = {
    "1m": 60_000,
    "3m": 180_000,
    "5m": 300_000,
    "15m": 900_000,
    "30m": 1_800_000,
    "1h": 3_600_000,
    "2h": 7_200_000,
    "4h": 14_400_000,
    "6h": 21_600_000,
    "8h": 28_800_000,
    "12h": 43_200_000,
    "1d": 86_400_000,
    "3d": 259_200_000,
    "1w": 604_800_000,
}


CONTINUOUS_MARKETS = {"CRYPTO"}


def _invalid(reason, *, candle_count=0):
    return {
        "status": "INVALID",
        "integrity_ok": False,
        "schema_valid": False,
        "ohlcv_valid": False,
        "timestamps_valid": False,
        "monotonic": False,
        "duplicates_clear": False,
        "interval_consistent": False,
        "gap_detected": False,
        "gap_count": 0,
        "off_interval_count": 0,
        "candle_count": candle_count,
        "expected_interval_ms": None,
        "observed_interval_ms": None,
        "max_gap_ms": 0,
        "reason": reason,
    }


def validate_candle_series(candles, interval, market_identity=None):
    """
    Validate a complete canonical candle series.

    Returns a deterministic diagnostic dictionary.
    The caller decides how the result feeds execution authorization.

    This function never silently repairs candles.
    """

    candle_count = len(candles) if isinstance(candles, list) else 0

    if not isinstance(candles, list):
        return _invalid(
            "Canonical candle series must be a list",
            candle_count=0,
        )

    if not candles:
        return _invalid(
            "Canonical candle series is empty",
            candle_count=0,
        )

    normalized_interval = str(interval or "").strip().lower()
    expected_interval_ms = INTERVAL_MS.get(normalized_interval)

    if expected_interval_ms is None:
        return {
            **_invalid(
                f"Unsupported canonical interval: {interval!r}",
                candle_count=candle_count,
            ),
            "expected_interval_ms": None,
        }

    schema_valid = True
    ohlcv_valid = True
    timestamps_valid = True
    monotonic = True
    duplicates_clear = True

    times = []
    close_times = []
    reason = None

    for index, candle in enumerate(candles):
        if not isinstance(candle, dict):
            schema_valid = False
            reason = reason or f"Candle at index {index} is not a dictionary"
            continue

        if tuple(candle.keys()) != EXPECTED_FIELDS:
            schema_valid = False
            reason = reason or (
                f"Candle field contract mismatch at index {index}"
            )
            continue

        try:
            timestamp = candle["time"]
            close_time = candle["close_time"]

            if isinstance(timestamp, bool) or isinstance(close_time, bool):
                raise ValueError("boolean timestamp")

            timestamp = int(timestamp)
            close_time = int(close_time)

            values = [
                float(candle["open"]),
                float(candle["high"]),
                float(candle["low"]),
                float(candle["close"]),
                float(candle["volume"]),
            ]
        except (KeyError, TypeError, ValueError, OverflowError):
            timestamps_valid = False
            ohlcv_valid = False
            reason = reason or (
                f"Candle at index {index} contains non-numeric data"
            )
            continue

        if (
            timestamp < 0
            or close_time < 0
            or close_time <= timestamp
        ):
            timestamps_valid = False
            reason = reason or (
                f"Candle at index {index} has invalid temporal bounds"
            )

        if not all(math.isfinite(value) for value in values):
            ohlcv_valid = False
            reason = reason or (
                f"Candle at index {index} contains non-finite OHLCV"
            )
        else:
            open_value, high_value, low_value, close_value, volume_value = values

            if (
                open_value <= 0
                or high_value <= 0
                or low_value <= 0
                or close_value <= 0
                or volume_value <= 0
            ):
                ohlcv_valid = False
                reason = reason or (
                    f"Candle at index {index} contains non-positive OHLCV"
                )

            if high_value < max(open_value, close_value):
                ohlcv_valid = False
                reason = reason or (
                    f"Candle at index {index} high is below open/close"
                )

            if low_value > min(open_value, close_value):
                ohlcv_valid = False
                reason = reason or (
                    f"Candle at index {index} low is above open/close"
                )

            if high_value <= low_value:
                ohlcv_valid = False
                reason = reason or (
                    f"Candle at index {index} high/low range is invalid"
                )

        times.append(timestamp)
        close_times.append(close_time)

    duplicates = len(times) != len(set(times))
    if duplicates:
        duplicates_clear = False
        reason = reason or "Duplicate candle timestamps detected"

    deltas = []
    if len(times) >= 2:
        previous = times[0]

        for timestamp in times[1:]:
            delta = timestamp - previous
            deltas.append(delta)

            if delta <= 0:
                monotonic = False

            previous = timestamp

    if not monotonic:
        timestamps_valid = False
        reason = reason or "Candle timestamps are not strictly increasing"

    if times:
        first = times[0]
        last = times[-1]
    else:
        first = None
        last = None

    off_interval_count = 0
    gap_count = 0
    max_gap_ms = 0

    for delta in deltas:
        if delta <= 0:
            continue

        if delta % expected_interval_ms != 0:
            off_interval_count += 1

        if delta > expected_interval_ms:
            gap_count += 1
            max_gap_ms = max(max_gap_ms, delta)

    interval_consistent = (
        bool(deltas)
        and off_interval_count == 0
        if len(times) >= 2
        else True
    )

    if not interval_consistent:
        reason = reason or (
            "Candle timestamps are inconsistent with requested interval"
        )

    observed_interval_ms = None
    if deltas:
        positive_deltas = [delta for delta in deltas if delta > 0]
        if positive_deltas:
            observed_interval_ms = Counter(
                positive_deltas
            ).most_common(1)[0][0]

    market = str(market_identity or "").upper().strip()

    # Continuous markets must not contain unexplained gaps.
    # Session-based markets retain gaps as explicit diagnostics because
    # overnight/weekend/session boundaries are legitimate.
    gap_policy = (
        "STRICT_CONTINUOUS"
        if market in CONTINUOUS_MARKETS
        else "SESSION_GAPS_ALLOWED"
    )

    gap_integrity_ok = (
        gap_count == 0
        if market in CONTINUOUS_MARKETS
        else True
    )

    if (
        market in CONTINUOUS_MARKETS
        and gap_count > 0
        and reason is None
    ):
        reason = "Unexpected candle gap detected"

    integrity_ok = all(
        (
            schema_valid,
            ohlcv_valid,
            timestamps_valid,
            monotonic,
            duplicates_clear,
            interval_consistent,
            gap_integrity_ok,
        )
    )

    if integrity_ok and gap_count > 0:
        status = "VALID_WITH_GAPS"
    elif integrity_ok:
        status = "VALID"
    else:
        status = "INVALID"

    return {
        "status": status,
        "integrity_ok": integrity_ok,
        "schema_valid": schema_valid,
        "ohlcv_valid": ohlcv_valid,
        "timestamps_valid": timestamps_valid,
        "monotonic": monotonic,
        "duplicates_clear": duplicates_clear,
        "interval_consistent": interval_consistent,
        "gap_detected": gap_count > 0,
        "gap_count": gap_count,
        "off_interval_count": off_interval_count,
        "candle_count": candle_count,
        "expected_interval_ms": expected_interval_ms,
        "observed_interval_ms": observed_interval_ms,
        "max_gap_ms": max_gap_ms,
        "first_candle_time": first,
        "last_candle_time": last,
        "gap_policy": gap_policy,
        "reason": reason,
    }
