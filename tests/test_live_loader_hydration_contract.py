"""
Jaguar Quant X Enterprise
Live Loader Hydration Contract

Purpose:
Prove that the canonical live-loader boundary:

- delegates live CRYPTO through MarketProvider
- declares explicit MCX intraday intent
- hydrates legacy MarketState scalar market fields
- preserves state object identity
- preserves state.market dictionary identity
- preserves existing analytical market context
- stores canonical candles without transformation
- fails closed on unsupported provider capabilities
- fails closed on invalid state and candle contracts

Network required: NO
"""

from core.market_state import MarketState

import market.live_loader as live_loader


EXPECTED_FIELDS = (
    "time",
    "close_time",
    "open",
    "high",
    "low",
    "close",
    "volume",
)


CANDLES = [
    {
        "time": 1000,
        "close_time": 1999,
        "open": 100.0,
        "high": 105.0,
        "low": 99.0,
        "close": 103.0,
        "volume": 1000.0,
    },
    {
        "time": 2000,
        "close_time": 2999,
        "open": 103.0,
        "high": 108.0,
        "low": 102.0,
        "close": 106.0,
        "volume": 1200.0,
    },
]


class FakeMarketProvider:
    calls = []

    @staticmethod
    def load(
        symbol,
        interval="15m",
        limit=500,
        *,
        intraday=None,
        to_date=None,
        from_date=None,
        as_of=None,
    ):

        FakeMarketProvider.calls.append(
            {
                "symbol": symbol,
                "interval": interval,
                "limit": limit,
                "intraday": intraday,
                "to_date": to_date,
                "from_date": from_date,
                "as_of": as_of,
            }
        )

        if symbol == "RELIANCE.NS":
            raise live_loader.MarketProviderError(
                "NSE provider capability is not implemented"
            )

        return [
            dict(candle)
            for candle in CANDLES
        ]


class InvalidListProvider:

    @staticmethod
    def load(
        *args,
        **kwargs,
    ):
        return {
            "price": 100.0,
        }


class EmptyProvider:

    @staticmethod
    def load(
        *args,
        **kwargs,
    ):
        return []


class InvalidFieldProvider:

    @staticmethod
    def load(
        *args,
        **kwargs,
    ):
        return [
            {
                "time": 1000,
                "close_time": 1999,
                "open": 100.0,
                "high": 105.0,
                "low": 99.0,
                "close": 103.0,
            }
        ]


def expect_error(
    failures,
    contract,
    function,
):

    try:
        function()

    except live_loader.LiveMarketLoaderError:
        return

    except Exception as exc:

        failures.append(
            {
                "contract": contract,
                "expected": "LiveMarketLoaderError",
                "actual": type(exc).__name__,
            }
        )

        return

    failures.append(
        {
            "contract": contract,
            "expected": "LiveMarketLoaderError",
            "actual": "NO_ERROR",
        }
    )


def main():

    failures = []

    original_provider = (
        live_loader.MarketProvider
    )

    try:

        live_loader.MarketProvider = (
            FakeMarketProvider
        )

        FakeMarketProvider.calls = []

        # ==================================================
        # CRYPTO LIVE HYDRATION
        # ==================================================

        state = MarketState()

        state.symbol = "BTCUSDT"
        state.timeframe = "15m"

        state.market["trend"] = "BULLISH"

        state_identity = id(
            state
        )

        market_identity = id(
            state.market
        )

        result = live_loader.update_state(
            state
        )

        if id(result) != state_identity:

            failures.append(
                {
                    "contract": "STATE_IDENTITY",
                    "expected": state_identity,
                    "actual": id(result),
                }
            )

        if id(state.market) != market_identity:

            failures.append(
                {
                    "contract": "MARKET_DICTIONARY_IDENTITY",
                    "expected": market_identity,
                    "actual": id(state.market),
                }
            )

        if state.market.get("trend") != "BULLISH":

            failures.append(
                {
                    "contract": "ANALYTICAL_CONTEXT_PRESERVATION",
                    "expected": "BULLISH",
                    "actual": state.market.get("trend"),
                }
            )

        expected_scalars = {
            "symbol": "BTCUSDT",
            "price": 106.0,
            "high": 108.0,
            "low": 102.0,
            "volume": 1200.0,
        }

        actual_scalars = {
            "symbol": state.symbol,
            "price": state.price,
            "high": state.high,
            "low": state.low,
            "volume": state.volume,
        }

        if actual_scalars != expected_scalars:

            failures.append(
                {
                    "contract": "LEGACY_SCALAR_HYDRATION",
                    "expected": expected_scalars,
                    "actual": actual_scalars,
                }
            )

        expected_market = {
            "market": "CRYPTO",
            "symbol": "BTCUSDT",
            "price": 106.0,
            "high": 108.0,
            "low": 102.0,
            "volume": 1200.0,
        }

        actual_market = {
            key: state.market.get(key)
            for key in expected_market
        }

        if actual_market != expected_market:

            failures.append(
                {
                    "contract": "MARKET_CONTEXT_HYDRATION",
                    "expected": expected_market,
                    "actual": actual_market,
                }
            )

        if state.market.get("candles") != CANDLES:

            failures.append(
                {
                    "contract": "CANONICAL_CANDLE_PRESERVATION",
                    "expected": CANDLES,
                    "actual": state.market.get("candles"),
                }
            )

        for candle in state.market.get(
            "candles",
            [],
        ):

            if tuple(candle.keys()) != EXPECTED_FIELDS:

                failures.append(
                    {
                        "contract": "CANONICAL_FIELDS",
                        "expected": EXPECTED_FIELDS,
                        "actual": tuple(candle.keys()),
                    }
                )

        if len(FakeMarketProvider.calls) != 1:

            failures.append(
                {
                    "contract": "CRYPTO_PROVIDER_CALL_COUNT",
                    "expected": 1,
                    "actual": len(
                        FakeMarketProvider.calls
                    ),
                }
            )

        else:

            crypto_call = (
                FakeMarketProvider.calls[0]
            )

            expected_crypto_call = {
                "symbol": "BTCUSDT",
                "interval": "15m",
                "limit": 300,
                "intraday": None,
                "to_date": None,
                "from_date": None,
                "as_of": None,
            }

            if crypto_call != expected_crypto_call:

                failures.append(
                    {
                        "contract": "CRYPTO_CANONICAL_DELEGATION",
                        "expected": expected_crypto_call,
                        "actual": crypto_call,
                    }
                )

        # ==================================================
        # MCX EXPLICIT LIVE TEMPORAL INTENT
        # ==================================================

        FakeMarketProvider.calls = []

        mcx_state = MarketState()

        mcx_state.symbol = "GOLDM"
        mcx_state.timeframe = "15m"

        live_loader.update_state(
            mcx_state
        )

        if len(FakeMarketProvider.calls) != 1:

            failures.append(
                {
                    "contract": "MCX_PROVIDER_CALL_COUNT",
                    "expected": 1,
                    "actual": len(
                        FakeMarketProvider.calls
                    ),
                }
            )

        else:

            mcx_call = (
                FakeMarketProvider.calls[0]
            )

            expected_mcx_call = {
                "symbol": "GOLDM",
                "interval": "15m",
                "limit": 300,
                "intraday": True,
                "to_date": None,
                "from_date": None,
                "as_of": None,
            }

            if mcx_call != expected_mcx_call:

                failures.append(
                    {
                        "contract": "MCX_EXPLICIT_INTRADAY_DELEGATION",
                        "expected": expected_mcx_call,
                        "actual": mcx_call,
                    }
                )

        if mcx_state.market.get("market") != "MCX":

            failures.append(
                {
                    "contract": "MCX_MARKET_IDENTITY",
                    "expected": "MCX",
                    "actual": mcx_state.market.get(
                        "market"
                    ),
                }
            )

        # ==================================================
        # EXPLICIT SYMBOL OVERRIDE
        # ==================================================

        override_state = MarketState()

        override_state.symbol = "ETHUSDT"
        override_state.timeframe = "4h"

        live_loader.update_state(
            override_state,
            "btcusdt",
            limit=2,
        )

        if override_state.symbol != "BTCUSDT":

            failures.append(
                {
                    "contract": "SYMBOL_OVERRIDE_NORMALIZATION",
                    "expected": "BTCUSDT",
                    "actual": override_state.symbol,
                }
            )

        override_call = (
            FakeMarketProvider.calls[-1]
        )

        if override_call.get("interval") != "4h":

            failures.append(
                {
                    "contract": "STATE_TIMEFRAME_DELEGATION",
                    "expected": "4h",
                    "actual": override_call.get(
                        "interval"
                    ),
                }
            )

        if override_call.get("limit") != 2:

            failures.append(
                {
                    "contract": "LIVE_LIMIT_DELEGATION",
                    "expected": 2,
                    "actual": override_call.get(
                        "limit"
                    ),
                }
            )

        # ==================================================
        # PROVIDER CAPABILITY FAIL CLOSED
        # ==================================================

        unsupported_state = MarketState()

        unsupported_state.symbol = "RELIANCE.NS"
        unsupported_state.timeframe = "15m"

        expect_error(
            failures,
            "UNSUPPORTED_PROVIDER_CAPABILITY",
            lambda: live_loader.update_state(
                unsupported_state
            ),
        )

        # ==================================================
        # INPUT / STATE FAIL CLOSED
        # ==================================================

        expect_error(
            failures,
            "MISSING_STATE",
            lambda: live_loader.update_state(
                None
            ),
        )

        missing_symbol_state = MarketState()

        missing_symbol_state.timeframe = "15m"

        expect_error(
            failures,
            "MISSING_SYMBOL",
            lambda: live_loader.update_state(
                missing_symbol_state
            ),
        )

        missing_timeframe_state = MarketState()

        missing_timeframe_state.symbol = "BTCUSDT"
        missing_timeframe_state.timeframe = ""

        expect_error(
            failures,
            "MISSING_TIMEFRAME",
            lambda: live_loader.update_state(
                missing_timeframe_state
            ),
        )

        invalid_market_state = MarketState()

        invalid_market_state.symbol = "BTCUSDT"
        invalid_market_state.timeframe = "15m"
        invalid_market_state.market = None

        expect_error(
            failures,
            "INVALID_MARKET_CONTEXT",
            lambda: live_loader.update_state(
                invalid_market_state
            ),
        )

        expect_error(
            failures,
            "BOOLEAN_LIMIT",
            lambda: live_loader.update_state(
                state,
                limit=True,
            ),
        )

        expect_error(
            failures,
            "ZERO_LIMIT",
            lambda: live_loader.update_state(
                state,
                limit=0,
            ),
        )

        # ==================================================
        # PROVIDER PAYLOAD FAIL CLOSED
        # ==================================================

        live_loader.MarketProvider = (
            InvalidListProvider
        )

        expect_error(
            failures,
            "NON_LIST_PROVIDER_PAYLOAD",
            lambda: live_loader.update_state(
                state
            ),
        )

        live_loader.MarketProvider = (
            EmptyProvider
        )

        expect_error(
            failures,
            "EMPTY_PROVIDER_PAYLOAD",
            lambda: live_loader.update_state(
                state
            ),
        )

        live_loader.MarketProvider = (
            InvalidFieldProvider
        )

        expect_error(
            failures,
            "INVALID_CANONICAL_FIELDS",
            lambda: live_loader.update_state(
                state
            ),
        )

    finally:

        live_loader.MarketProvider = (
            original_provider
        )

    if failures:

        print(
            "LIVE_LOADER_HYDRATION_CONTRACT: FAIL"
        )

        for failure in failures:
            print(failure)

        raise SystemExit(1)

    print(
        "LIVE_LOADER_HYDRATION_CONTRACT: PASS"
    )

    print(
        "Canonical provider delegation: PASS"
    )

    print(
        "CRYPTO live routing: PASS"
    )

    print(
        "MCX explicit intraday routing: PASS"
    )

    print(
        "Legacy scalar hydration: PASS"
    )

    print(
        "State identity preservation: PASS"
    )

    print(
        "Market dictionary identity preservation: PASS"
    )

    print(
        "Analytical context preservation: PASS"
    )

    print(
        "Canonical candle preservation: PASS"
    )

    print(
        "Fail-closed cases: 9"
    )

    print(
        "Network required: NO"
    )


if __name__ == "__main__":
    main()
