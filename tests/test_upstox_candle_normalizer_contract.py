"""
Jaguar Quant X Enterprise
Upstox Candle Normalizer Contract v1

Purpose:
Prove deterministic conversion from synthetic Upstox candle
arrays into Jaguar's canonical seven-field candle contract.

No credential is required.
No network request is executed.
"""

from market.upstox_candle_normalizer import (
    UpstoxCandleNormalizationError,
    UpstoxCandleNormalizer,
)
from market.upstox_timeframe import (
    UpstoxTimeframeAdapter,
)


RAW_PAYLOAD = {
    "status": "success",
    "data": {
        "candles": [
            [
                "2026-07-14T09:30:00+05:30",
                101.5,
                106.0,
                100.0,
                104.25,
                12500,
                777,
            ],
            [
                "2026-07-14T09:15:00+05:30",
                "100.0",
                "103.5",
                "99.5",
                "101.5",
                "10000",
                "555",
            ],
        ]
    },
}


EXPECTED_FIELDS = (
    "time",
    "close_time",
    "open",
    "high",
    "low",
    "close",
    "volume",
)


def main():

    failures = []

    timeframe = (
        UpstoxTimeframeAdapter.parse(
            "15m"
        )
    )

    candles = (
        UpstoxCandleNormalizer
        .normalize_payload(
            RAW_PAYLOAD,
            timeframe,
        )
    )

    # ======================================================
    # COLLECTION CONTRACT
    # ======================================================

    if len(candles) != 2:

        failures.append(
            {
                "contract": "CANDLE_COUNT",
                "expected": 2,
                "actual": len(candles),
            }
        )

    # ======================================================
    # ASCENDING CANONICAL IDENTITY
    # ======================================================

    times = [
        candle["time"]
        for candle in candles
    ]

    if times != sorted(times):

        failures.append(
            {
                "contract": "ASCENDING_TIME",
                "actual": times,
            }
        )

    # ======================================================
    # EXACT FIELD CONTRACT
    # ======================================================

    for candle in candles:

        actual_fields = tuple(
            candle.keys()
        )

        if actual_fields != EXPECTED_FIELDS:

            failures.append(
                {
                    "contract": "FIELD_CONTRACT",
                    "expected": EXPECTED_FIELDS,
                    "actual": actual_fields,
                }
            )

    # ======================================================
    # NUMERIC CONTRACT
    # ======================================================

    first = candles[0]

    expected_numeric = {
        "open": 100.0,
        "high": 103.5,
        "low": 99.5,
        "close": 101.5,
        "volume": 10000.0,
    }

    for field, expected in (
        expected_numeric.items()
    ):

        actual = first[field]

        if actual != expected:

            failures.append(
                {
                    "contract": "NUMERIC_NORMALIZATION",
                    "field": field,
                    "expected": expected,
                    "actual": actual,
                }
            )

        if not isinstance(actual, float):

            failures.append(
                {
                    "contract": "NUMERIC_TYPE",
                    "field": field,
                    "actual": type(actual).__name__,
                }
            )

    # ======================================================
    # CLOSE-TIME CONTRACT
    # ======================================================

    expected_duration = (
        15
        * 60
        * 1000
    )

    for candle in candles:

        actual_duration = (
            candle["close_time"]
            - candle["time"]
            + 1
        )

        if actual_duration != expected_duration:

            failures.append(
                {
                    "contract": "CLOSE_TIME",
                    "expected": expected_duration,
                    "actual": actual_duration,
                }
            )

    # ======================================================
    # OPEN INTEREST EXCLUSION
    # ======================================================

    for candle in candles:

        if "open_interest" in candle:

            failures.append(
                {
                    "contract": "OPEN_INTEREST_EXCLUSION",
                    "actual": candle,
                }
            )

    # ======================================================
    # MONTH FAILS CLOSED
    # ======================================================

    monthly_timeframe = (
        UpstoxTimeframeAdapter.parse(
            "1mo"
        )
    )

    try:

        UpstoxCandleNormalizer.normalize_payload(
            RAW_PAYLOAD,
            monthly_timeframe,
        )

    except UpstoxCandleNormalizationError:
        pass

    else:

        failures.append(
            {
                "contract": "CALENDAR_MONTH_FAIL_CLOSED",
                "actual": "NORMALIZATION ALLOWED",
            }
        )

    # ======================================================
    # DUPLICATE CANDLE IDENTITY FAILS CLOSED
    # ======================================================

    duplicate_payload = {
        "data": {
            "candles": [
                RAW_PAYLOAD["data"]["candles"][0],
                RAW_PAYLOAD["data"]["candles"][0],
            ]
        }
    }

    try:

        UpstoxCandleNormalizer.normalize_payload(
            duplicate_payload,
            timeframe,
        )

    except UpstoxCandleNormalizationError:
        pass

    else:

        failures.append(
            {
                "contract": "DUPLICATE_IDENTITY_FAIL_CLOSED",
                "actual": "DUPLICATE ALLOWED",
            }
        )

    # ======================================================
    # INVALID CANDLE FAILS CLOSED
    # ======================================================

    invalid_payload = {
        "data": {
            "candles": [
                [
                    "2026-07-14T09:15:00+05:30",
                    100,
                    103,
                    99,
                    "NOT_A_PRICE",
                    10000,
                ]
            ]
        }
    }

    try:

        UpstoxCandleNormalizer.normalize_payload(
            invalid_payload,
            timeframe,
        )

    except UpstoxCandleNormalizationError:
        pass

    else:

        failures.append(
            {
                "contract": "INVALID_NUMERIC_FAIL_CLOSED",
                "actual": "INVALID CANDLE ALLOWED",
            }
        )

    # ======================================================
    # RESULT
    # ======================================================

    if failures:

        print(
            "UPSTOX_CANDLE_NORMALIZER_CONTRACT: FAIL"
        )

        for failure in failures:

            print(
                "FAIL:",
                failure,
            )

        raise AssertionError(
            "Upstox candle normalizer contract violated"
        )

    print(
        "UPSTOX_CANDLE_NORMALIZER_CONTRACT: PASS"
    )

    print(
        "Canonical fields:",
        len(EXPECTED_FIELDS),
    )

    print(
        "Normalized candles:",
        len(candles),
    )

    print(
        "Ascending identity: PASS"
    )

    print(
        "Close-time derivation: PASS"
    )

    print(
        "Open-interest exclusion: PASS"
    )

    print(
        "Calendar-month fail-closed: PASS"
    )

    print(
        "Duplicate identity fail-closed: PASS"
    )

    print(
        "Invalid numeric fail-closed: PASS"
    )

    print(
        "Network required: NO"
    )


if __name__ == "__main__":
    main()
