"""
Jaguar Quant X Enterprise
Market Provider Routing Contract v1

Purpose:
Prove exchange-aware canonical provider routing.

The contract verifies:
- CRYPTO delegates to canonical Binance candle loading
- MCX delegates to the canonical Upstox MCX provider
- MCX temporal intent remains explicit
- NSE / BSE / FOREX / US fail closed
- UNKNOWN fails closed
- existing three-positional-argument CRYPTO calls remain valid

No credential is required.
No network request is executed.
"""

from datetime import date
from unittest.mock import patch

from market.provider import (
    MarketProvider,
    MarketProviderError,
)


CANONICAL_CANDLES = [
    {
        "time": 1000,
        "close_time": 1999,
        "open": 100.0,
        "high": 105.0,
        "low": 99.0,
        "close": 103.0,
        "volume": 10000.0,
    },
    {
        "time": 2000,
        "close_time": 2999,
        "open": 103.0,
        "high": 107.0,
        "low": 102.0,
        "close": 106.0,
        "volume": 13000.0,
    },
]


class FakeUpstoxProvider:

    calls = []

    def __init__(self):
        self.__class__.calls.append(
            {
                "method": "__init__",
            }
        )

    def load_mcx(
        self,
        family,
        interval="15m",
        limit=300,
        to_date=None,
        from_date=None,
        as_of=None,
        intraday=False,
    ):
        self.__class__.calls.append(
            {
                "method": "load_mcx",
                "family": family,
                "interval": interval,
                "limit": limit,
                "to_date": to_date,
                "from_date": from_date,
                "as_of": as_of,
                "intraday": intraday,
            }
        )

        return CANONICAL_CANDLES


def main():

    failures = []

    # ======================================================
    # CRYPTO ROUTING
    # ======================================================

    crypto_calls = []

    def fake_get_klines(
        symbol,
        interval,
        limit,
    ):
        crypto_calls.append(
            {
                "symbol": symbol,
                "interval": interval,
                "limit": limit,
            }
        )

        return CANONICAL_CANDLES

    with patch(
        "market.provider.get_klines",
        new=fake_get_klines,
    ):

        candles = MarketProvider.load(
            "BTCUSDT",
            "15m",
            500,
        )

    if candles is not CANONICAL_CANDLES:

        failures.append(
            {
                "contract": "CRYPTO_RETURN_IDENTITY",
                "actual": candles,
            }
        )

    expected_crypto_calls = [
        {
            "symbol": "BTCUSDT",
            "interval": "15m",
            "limit": 500,
        }
    ]

    if crypto_calls != expected_crypto_calls:

        failures.append(
            {
                "contract": "CRYPTO_DELEGATION",
                "expected": expected_crypto_calls,
                "actual": crypto_calls,
            }
        )

    # ======================================================
    # MCX INTRADAY ROUTING
    # ======================================================

    FakeUpstoxProvider.calls = []

    with patch(
        "market.upstox_provider.UpstoxProvider",
        new=FakeUpstoxProvider,
    ):

        candles = MarketProvider.load(
            "GOLDM",
            "15m",
            300,
            intraday=True,
            as_of=date(
                2026,
                7,
                14,
            ),
        )

    if candles is not CANONICAL_CANDLES:

        failures.append(
            {
                "contract": "MCX_INTRADAY_RETURN_IDENTITY",
                "actual": candles,
            }
        )

    expected_intraday_calls = [
        {
            "method": "__init__",
        },
        {
            "method": "load_mcx",
            "family": "GOLDM",
            "interval": "15m",
            "limit": 300,
            "to_date": None,
            "from_date": None,
            "as_of": date(
                2026,
                7,
                14,
            ),
            "intraday": True,
        },
    ]

    if (
        FakeUpstoxProvider.calls
        != expected_intraday_calls
    ):

        failures.append(
            {
                "contract": "MCX_INTRADAY_DELEGATION",
                "expected": expected_intraday_calls,
                "actual": FakeUpstoxProvider.calls,
            }
        )

    # ======================================================
    # MCX HISTORICAL ROUTING
    # ======================================================

    FakeUpstoxProvider.calls = []

    with patch(
        "market.upstox_provider.UpstoxProvider",
        new=FakeUpstoxProvider,
    ):

        candles = MarketProvider.load(
            "SILVERM",
            "30m",
            200,
            intraday=False,
            to_date="2026-07-14",
            from_date="2026-07-01",
            as_of=date(
                2026,
                7,
                14,
            ),
        )

    if candles is not CANONICAL_CANDLES:

        failures.append(
            {
                "contract": "MCX_HISTORICAL_RETURN_IDENTITY",
                "actual": candles,
            }
        )

    expected_historical_call = {
        "method": "load_mcx",
        "family": "SILVERM",
        "interval": "30m",
        "limit": 200,
        "to_date": "2026-07-14",
        "from_date": "2026-07-01",
        "as_of": date(
            2026,
            7,
            14,
        ),
        "intraday": False,
    }

    if (
        len(FakeUpstoxProvider.calls) != 2
        or FakeUpstoxProvider.calls[1]
        != expected_historical_call
    ):

        failures.append(
            {
                "contract": "MCX_HISTORICAL_DELEGATION",
                "expected": expected_historical_call,
                "actual": FakeUpstoxProvider.calls,
            }
        )

    # ======================================================
    # FAIL-CLOSED ROUTING
    # ======================================================

    fail_closed_cases = []

    cases = [
        (
            "MCX_EXPLICIT_MODE",
            lambda: MarketProvider.load(
                "GOLD",
                "15m",
                300,
            ),
        ),
        (
            "MCX_BOOLEAN_MODE",
            lambda: MarketProvider.load(
                "GOLD",
                "15m",
                300,
                intraday="true",
            ),
        ),
        (
            "CRYPTO_TEMPORAL_ARGUMENTS",
            lambda: MarketProvider.load(
                "BTCUSDT",
                "15m",
                300,
                intraday=True,
            ),
        ),
        (
            "NSE_CAPABILITY",
            lambda: MarketProvider.load(
                "RELIANCE.NS",
            ),
        ),
        (
            "BSE_CAPABILITY",
            lambda: MarketProvider.load(
                "SBIN.BO",
            ),
        ),
        (
            "FOREX_CAPABILITY",
            lambda: MarketProvider.load(
                "EURUSD",
            ),
        ),
        (
            "US_CAPABILITY",
            lambda: MarketProvider.load(
                "AAPL",
            ),
        ),
        (
            "UNKNOWN_IDENTITY",
            lambda: MarketProvider.load(
                "UNKNOWN123",
            ),
        ),
        (
            "NONE_IDENTITY",
            lambda: MarketProvider.load(
                None,
            ),
        ),
    ]

    for name, operation in cases:

        try:
            operation()

        except MarketProviderError:
            fail_closed_cases.append(
                name
            )

        else:
            failures.append(
                {
                    "contract": name,
                    "actual": "ROUTING ALLOWED",
                }
            )

    # ======================================================
    # RESULT
    # ======================================================

    if failures:

        print(
            "MARKET_PROVIDER_ROUTING_CONTRACT: FAIL"
        )

        for failure in failures:

            print(
                "FAIL:",
                failure,
            )

        raise AssertionError(
            "Market provider routing contract violated"
        )

    print(
        "MARKET_PROVIDER_ROUTING_CONTRACT: PASS"
    )

    print(
        "Crypto canonical delegation: PASS"
    )

    print(
        "Legacy three-argument crypto interface: PASS"
    )

    print(
        "MCX intraday delegation: PASS"
    )

    print(
        "MCX historical delegation: PASS"
    )

    print(
        "Explicit MCX temporal intent: PASS"
    )

    print(
        "Unsupported capability fail-closed cases:",
        len(fail_closed_cases),
    )

    print(
        "Network required: NO"
    )


if __name__ == "__main__":
    main()
