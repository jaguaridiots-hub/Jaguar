"""
Jaguar Quant X Enterprise
Upstox Provider Contract v1

Purpose:
Prove deterministic orchestration across:
- timeframe adapter
- instrument search
- MCX futures resolver
- candle transport boundary
- canonical candle normalizer
- canonical candle limit

All provider responses are synthetic.
No credential is required.
No network request is executed.
"""

from datetime import date

from market.upstox_provider import (
    UpstoxProvider,
    UpstoxProviderError,
)


AS_OF = date(
    2026,
    7,
    14,
)


SEARCH_PAYLOAD = {
    "status": "success",
    "data": [
        {
            "exchange": "MCX",
            "segment": "MCX_FO",
            "instrument_type": "FUT",
            "trading_symbol": "GOLDM 05OCT26 FUT",
            "expiry": "2026-10-05",
            "instrument_key": "MCX_FO|GOLDM_OCT",
        },
        {
            "exchange": "MCX",
            "segment": "MCX_FO",
            "instrument_type": "FUT",
            "trading_symbol": "GOLDM 05AUG26 FUT",
            "expiry": "2026-08-05",
            "instrument_key": "MCX_FO|GOLDM_AUG",
        },
        {
            "exchange": "MCX",
            "segment": "MCX_FO",
            "instrument_type": "FUT",
            "trading_symbol": "GOLD 05AUG26 FUT",
            "expiry": "2026-08-05",
            "instrument_key": "MCX_FO|GOLD_AUG",
        },
    ],
}


CANDLE_PAYLOAD = {
    "status": "success",
    "data": {
        "candles": [
            [
                "2026-07-14T09:45:00+05:30",
                103,
                107,
                102,
                106,
                13000,
                900,
            ],
            [
                "2026-07-14T09:30:00+05:30",
                101,
                105,
                100,
                103,
                12000,
                800,
            ],
            [
                "2026-07-14T09:15:00+05:30",
                100,
                103,
                99,
                101,
                10000,
                700,
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


class FakeTransport:

    def __init__(self):
        self.calls = []

    def search_instruments(
        self,
        query,
        exchange=None,
        segment=None,
        instrument_type=None,
    ):
        self.calls.append(
            {
                "method": "search_instruments",
                "query": query,
                "exchange": exchange,
                "segment": segment,
                "instrument_type": instrument_type,
            }
        )

        return SEARCH_PAYLOAD

    def historical_candles(
        self,
        instrument_key,
        unit,
        interval,
        to_date,
        from_date,
    ):
        self.calls.append(
            {
                "method": "historical_candles",
                "instrument_key": instrument_key,
                "unit": unit,
                "interval": interval,
                "to_date": to_date,
                "from_date": from_date,
            }
        )

        return CANDLE_PAYLOAD

    def intraday_candles(
        self,
        instrument_key,
        unit,
        interval,
    ):
        self.calls.append(
            {
                "method": "intraday_candles",
                "instrument_key": instrument_key,
                "unit": unit,
                "interval": interval,
            }
        )

        return CANDLE_PAYLOAD


def main():

    failures = []

    # ======================================================
    # HISTORICAL PROVIDER PIPELINE
    # ======================================================

    historical_transport = FakeTransport()

    historical_provider = UpstoxProvider(
        transport=historical_transport
    )

    candles = historical_provider.load_mcx(
        family="GOLDM",
        interval="15m",
        limit=2,
        to_date="2026-07-14",
        from_date="2026-07-01",
        as_of=AS_OF,
    )

    if len(candles) != 2:

        failures.append(
            {
                "contract": "HISTORICAL_LIMIT",
                "expected": 2,
                "actual": len(candles),
            }
        )

    if len(historical_transport.calls) != 2:

        failures.append(
            {
                "contract": "HISTORICAL_CALL_COUNT",
                "expected": 2,
                "actual": len(
                    historical_transport.calls
                ),
            }
        )

    else:

        search_call = (
            historical_transport.calls[0]
        )

        candle_call = (
            historical_transport.calls[1]
        )

        expected_search = {
            "method": "search_instruments",
            "query": "GOLDM",
            "exchange": "MCX",
            "segment": "MCX_FO",
            "instrument_type": "FUT",
        }

        if search_call != expected_search:

            failures.append(
                {
                    "contract": "SEARCH_DELEGATION",
                    "expected": expected_search,
                    "actual": search_call,
                }
            )

        if (
            candle_call.get("instrument_key")
            != "MCX_FO|GOLDM_AUG"
        ):

            failures.append(
                {
                    "contract": "RESOLVED_INSTRUMENT",
                    "expected": "MCX_FO|GOLDM_AUG",
                    "actual": candle_call.get(
                        "instrument_key"
                    ),
                }
            )

        if candle_call.get("unit") != "minutes":

            failures.append(
                {
                    "contract": "TIMEFRAME_UNIT",
                    "expected": "minutes",
                    "actual": candle_call.get("unit"),
                }
            )

        if candle_call.get("interval") != 15:

            failures.append(
                {
                    "contract": "TIMEFRAME_INTERVAL",
                    "expected": 15,
                    "actual": candle_call.get(
                        "interval"
                    ),
                }
            )

    # ======================================================
    # CANONICAL CANDLE CONTRACT
    # ======================================================

    for candle in candles:

        actual_fields = tuple(
            candle.keys()
        )

        if actual_fields != EXPECTED_FIELDS:

            failures.append(
                {
                    "contract": "CANONICAL_FIELDS",
                    "expected": EXPECTED_FIELDS,
                    "actual": actual_fields,
                }
            )

    times = [
        candle["time"]
        for candle in candles
    ]

    if times != sorted(times):

        failures.append(
            {
                "contract": "ASCENDING_IDENTITY",
                "actual": times,
            }
        )

    if candles[-1]["close"] != 106.0:

        failures.append(
            {
                "contract": "LATEST_CANDLE_PRESERVED",
                "expected": 106.0,
                "actual": candles[-1]["close"],
            }
        )

    # ======================================================
    # INTRADAY PROVIDER PIPELINE
    # ======================================================

    intraday_transport = FakeTransport()

    intraday_provider = UpstoxProvider(
        transport=intraday_transport
    )

    intraday_candles = (
        intraday_provider.load_mcx(
            family="GOLDM",
            interval="15m",
            limit=300,
            as_of=AS_OF,
            intraday=True,
        )
    )

    if len(intraday_candles) != 3:

        failures.append(
            {
                "contract": "INTRADAY_CANDLE_COUNT",
                "expected": 3,
                "actual": len(
                    intraday_candles
                ),
            }
        )

    if len(intraday_transport.calls) != 2:

        failures.append(
            {
                "contract": "INTRADAY_CALL_COUNT",
                "expected": 2,
                "actual": len(
                    intraday_transport.calls
                ),
            }
        )

    elif (
        intraday_transport.calls[1].get("method")
        != "intraday_candles"
    ):

        failures.append(
            {
                "contract": "INTRADAY_DELEGATION",
                "expected": "intraday_candles",
                "actual": (
                    intraday_transport.calls[1]
                ),
            }
        )

    # ======================================================
    # FAIL-CLOSED CONTRACTS
    # ======================================================

    fail_closed_cases = 0

    try:

        historical_provider.load_mcx(
            family="GOLDM",
            interval="15m",
            limit=0,
            to_date="2026-07-14",
            from_date="2026-07-01",
            as_of=AS_OF,
        )

    except UpstoxProviderError:
        fail_closed_cases += 1

    else:

        failures.append(
            {
                "contract": "ZERO_LIMIT_FAIL_CLOSED",
                "actual": "LOAD ALLOWED",
            }
        )

    try:

        historical_provider.load_mcx(
            family="GOLDM",
            interval="15m",
            limit=300,
            as_of=AS_OF,
        )

    except UpstoxProviderError:
        fail_closed_cases += 1

    else:

        failures.append(
            {
                "contract": "MISSING_DATES_FAIL_CLOSED",
                "actual": "LOAD ALLOWED",
            }
        )

    try:

        historical_provider.load_mcx(
            family="GOLDM",
            interval="15m",
            limit=300,
            to_date="2026-07-01",
            from_date="2026-07-14",
            as_of=AS_OF,
        )

    except UpstoxProviderError:
        fail_closed_cases += 1

    else:

        failures.append(
            {
                "contract": "DATE_ORDER_FAIL_CLOSED",
                "actual": "LOAD ALLOWED",
            }
        )

    try:

        intraday_provider.load_mcx(
            family="GOLDM",
            interval="15m",
            limit=300,
            to_date="2026-07-14",
            as_of=AS_OF,
            intraday=True,
        )

    except UpstoxProviderError:
        fail_closed_cases += 1

    else:

        failures.append(
            {
                "contract": "INTRADAY_DATE_FAIL_CLOSED",
                "actual": "LOAD ALLOWED",
            }
        )

    # ======================================================
    # RESULT
    # ======================================================

    if failures:

        print(
            "UPSTOX_PROVIDER_CONTRACT: FAIL"
        )

        for failure in failures:

            print(
                "FAIL:",
                failure,
            )

        raise AssertionError(
            "Upstox provider contract violated"
        )

    print(
        "UPSTOX_PROVIDER_CONTRACT: PASS"
    )

    print(
        "Historical orchestration: PASS"
    )

    print(
        "Intraday orchestration: PASS"
    )

    print(
        "Nearest-expiry resolution: PASS"
    )

    print(
        "Canonical timeframe delegation: PASS"
    )

    print(
        "Canonical candle fields:",
        len(EXPECTED_FIELDS),
    )

    print(
        "Canonical limit preservation: PASS"
    )

    print(
        "Fail-closed cases:",
        fail_closed_cases,
    )

    print(
        "Network required: NO"
    )


if __name__ == "__main__":
    main()
