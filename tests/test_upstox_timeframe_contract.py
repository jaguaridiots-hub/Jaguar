"""
Jaguar Quant X Enterprise
Upstox Timeframe Contract v1

Purpose:
Prove deterministic translation from Jaguar timeframe
identities into Upstox Candle V3 unit/interval grammar.

No credential is required.
No network request is executed.
"""


from market.upstox_timeframe import (
    UpstoxTimeframeAdapter,
    UpstoxTimeframeError,
)


EXPECTED_TIMEFRAMES = {
    "1m": ("minutes", 1),
    "3m": ("minutes", 3),
    "5m": ("minutes", 5),
    "15m": ("minutes", 15),
    "30m": ("minutes", 30),
    "60m": ("minutes", 60),
    "300m": ("minutes", 300),
    "1h": ("hours", 1),
    "2h": ("hours", 2),
    "4h": ("hours", 4),
    "5h": ("hours", 5),
    "1d": ("days", 1),
    "1w": ("weeks", 1),
    "1mo": ("months", 1),
}


NORMALIZED_TIMEFRAMES = {
    " 15M ": ("minutes", 15),
    " 4H ": ("hours", 4),
    " 1D ": ("days", 1),
    " 1W ": ("weeks", 1),
    " 1MO ": ("months", 1),
}


UNSUPPORTED_TIMEFRAMES = (
    None,
    "",
    " ",
    "0m",
    "301m",
    "0h",
    "6h",
    "2d",
    "2w",
    "2mo",
    "15",
    "minute",
    "15minute",
    "1y",
)


def main():

    failures = []

    # ======================================================
    # CANONICAL MAPPINGS
    # ======================================================

    for timeframe, expected in (
        EXPECTED_TIMEFRAMES.items()
    ):

        actual = (
            UpstoxTimeframeAdapter
            .parse(timeframe)
            .as_tuple()
        )

        if actual != expected:

            failures.append(
                {
                    "contract": "CANONICAL_MAPPING",
                    "timeframe": timeframe,
                    "expected": expected,
                    "actual": actual,
                }
            )

    # ======================================================
    # NORMALIZATION
    # ======================================================

    for timeframe, expected in (
        NORMALIZED_TIMEFRAMES.items()
    ):

        actual = (
            UpstoxTimeframeAdapter
            .parse(timeframe)
            .as_tuple()
        )

        if actual != expected:

            failures.append(
                {
                    "contract": "NORMALIZATION",
                    "timeframe": timeframe,
                    "expected": expected,
                    "actual": actual,
                }
            )

    # ======================================================
    # FAIL-CLOSED UNSUPPORTED VALUES
    # ======================================================

    for timeframe in UNSUPPORTED_TIMEFRAMES:

        try:

            UpstoxTimeframeAdapter.parse(
                timeframe
            )

        except UpstoxTimeframeError:
            pass

        else:

            failures.append(
                {
                    "contract": "FAIL_CLOSED",
                    "timeframe": timeframe,
                    "actual": "TIMEFRAME ALLOWED",
                }
            )

    # ======================================================
    # RESULT
    # ======================================================

    if failures:

        print(
            "UPSTOX_TIMEFRAME_CONTRACT: FAIL"
        )

        for failure in failures:

            print(
                "FAIL:",
                failure,
            )

        raise AssertionError(
            "Upstox timeframe contract violated"
        )

    print(
        "UPSTOX_TIMEFRAME_CONTRACT: PASS"
    )

    print(
        "Canonical mappings:",
        len(EXPECTED_TIMEFRAMES),
    )

    print(
        "Normalization cases:",
        len(NORMALIZED_TIMEFRAMES),
    )

    print(
        "Fail-closed cases:",
        len(UNSUPPORTED_TIMEFRAMES),
    )

    print(
        "Network required: NO"
    )


if __name__ == "__main__":
    main()
