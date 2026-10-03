"""
Jaguar Quant X Enterprise
Upstox Instrument Resolver Contract v1

Purpose:
Prove deterministic MCX commodity-family resolution from
provider candidate records.

All instrument records are synthetic.
No credential is required.
No network request is executed.
"""

from datetime import date

from market.upstox_instrument_resolver import (
    UpstoxInstrumentResolutionError,
    UpstoxInstrumentResolver,
)


AS_OF = date(
    2026,
    7,
    14,
)


CANDIDATES = [
    # ======================================================
    # GOLD
    # ======================================================
    {
        "exchange": "MCX",
        "segment": "MCX_FO",
        "instrument_type": "FUT",
        "trading_symbol": "GOLD 05AUG26 FUT",
        "expiry": "2026-08-05",
        "instrument_key": "MCX_FO|GOLD_AUG",
    },
    {
        "exchange": "MCX",
        "segment": "MCX_FO",
        "instrument_type": "FUT",
        "trading_symbol": "GOLD 05OCT26 FUT",
        "expiry": "2026-10-05",
        "instrument_key": "MCX_FO|GOLD_OCT",
    },

    # ======================================================
    # GOLD MINI
    # ======================================================
    {
        "exchange": "MCX",
        "segment": "MCX_FO",
        "instrument_type": "FUTURE",
        "trading_symbol": "GOLDM 05AUG26 FUT",
        "expiry": "2026-08-05",
        "instrument_key": "MCX_FO|GOLDM_AUG",
    },

    # ======================================================
    # SILVER
    # ======================================================
    {
        "exchange": "MCX",
        "segment": "MCX_FO",
        "instrument_type": "FUTURES",
        "trading_symbol": "SILVER 04SEP26 FUT",
        "expiry": "2026-09-04",
        "instrument_key": "MCX_FO|SILVER_SEP",
    },

    # ======================================================
    # SILVER MINI
    # ======================================================
    {
        "exchange": "MCX",
        "segment": "MCX_FO",
        "instrument_type": "FUT",
        "trading_symbol": "SILVERM 31AUG26 FUT",
        "expiry": "2026-08-31",
        "instrument_key": "MCX_FO|SILVERM_AUG",
    },

    # ======================================================
    # ENERGY
    # ======================================================
    {
        "exchange": "MCX",
        "segment": "MCX_FO",
        "instrument_type": "FUT",
        "trading_symbol": "CRUDEOILM 19AUG26 FUT",
        "expiry": "2026-08-19",
        "instrument_key": "MCX_FO|CRUDEOILM_AUG",
    },
    {
        "exchange": "MCX",
        "segment": "MCX_FO",
        "instrument_type": "FUT",
        "trading_symbol": "NATGASMINI 25AUG26 FUT",
        "expiry": "2026-08-25",
        "instrument_key": "MCX_FO|NATGASMINI_AUG",
    },

    # ======================================================
    # EXPIRED GOLD — MUST BE REJECTED
    # ======================================================
    {
        "exchange": "MCX",
        "segment": "MCX_FO",
        "instrument_type": "FUT",
        "trading_symbol": "GOLD 05JUN26 FUT",
        "expiry": "2026-06-05",
        "instrument_key": "MCX_FO|GOLD_EXPIRED",
    },

    # ======================================================
    # WRONG EXCHANGE
    # ======================================================
    {
        "exchange": "NSE",
        "segment": "NSE_FO",
        "instrument_type": "FUT",
        "trading_symbol": "GOLD 01AUG26 FUT",
        "expiry": "2026-08-01",
        "instrument_key": "NSE_FO|WRONG_EXCHANGE",
    },

    # ======================================================
    # WRONG SEGMENT
    # ======================================================
    {
        "exchange": "MCX",
        "segment": "MCX_EQ",
        "instrument_type": "FUT",
        "trading_symbol": "GOLD 01AUG26 FUT",
        "expiry": "2026-08-01",
        "instrument_key": "MCX_EQ|WRONG_SEGMENT",
    },

    # ======================================================
    # OPTION — MUST BE REJECTED
    # ======================================================
    {
        "exchange": "MCX",
        "segment": "MCX_FO",
        "instrument_type": "CE",
        "trading_symbol": "GOLD 01AUG26 100000 CE",
        "expiry": "2026-08-01",
        "instrument_key": "MCX_FO|GOLD_OPTION",
    },

    # ======================================================
    # MISSING KEY — MUST BE REJECTED
    # ======================================================
    {
        "exchange": "MCX",
        "segment": "MCX_FO",
        "instrument_type": "FUT",
        "trading_symbol": "GOLD 20JUL26 FUT",
        "expiry": "2026-07-20",
        "instrument_key": "",
    },
]


EXPECTED_RESOLUTIONS = {
    "GOLD": "MCX_FO|GOLD_AUG",
    "GOLDM": "MCX_FO|GOLDM_AUG",
    "SILVER": "MCX_FO|SILVER_SEP",
    "SILVERM": "MCX_FO|SILVERM_AUG",
    "CRUDEOILM": "MCX_FO|CRUDEOILM_AUG",
    "NATGASMINI": "MCX_FO|NATGASMINI_AUG",
}


FAIL_CLOSED_FAMILIES = (
    "UNKNOWN",
    "XAUUSD",
    "",
    None,
)


def main():

    failures = []

    # ======================================================
    # DETERMINISTIC FAMILY RESOLUTION
    # ======================================================

    for family, expected_key in (
        EXPECTED_RESOLUTIONS.items()
    ):

        record = (
            UpstoxInstrumentResolver
            .resolve_mcx_future(
                family=family,
                candidates=CANDIDATES,
                as_of=AS_OF,
            )
        )

        actual_key = record.get(
            "instrument_key"
        )

        if actual_key != expected_key:

            failures.append(
                {
                    "contract": "FAMILY_RESOLUTION",
                    "family": family,
                    "expected": expected_key,
                    "actual": actual_key,
                }
            )

    # ======================================================
    # GOLD MUST NOT COLLIDE WITH GOLDM
    # ======================================================

    gold_record = (
        UpstoxInstrumentResolver
        .resolve_mcx_future(
            family="GOLD",
            candidates=CANDIDATES,
            as_of=AS_OF,
        )
    )

    if (
        gold_record.get("instrument_key")
        != "MCX_FO|GOLD_AUG"
    ):

        failures.append(
            {
                "contract": "FAMILY_COLLISION",
                "family": "GOLD",
                "actual": gold_record.get(
                    "instrument_key"
                ),
            }
        )

    # ======================================================
    # FAIL-CLOSED UNSUPPORTED FAMILIES
    # ======================================================

    for family in FAIL_CLOSED_FAMILIES:

        try:

            UpstoxInstrumentResolver.resolve_mcx_future(
                family=family,
                candidates=CANDIDATES,
                as_of=AS_OF,
            )

        except UpstoxInstrumentResolutionError:
            pass

        else:

            failures.append(
                {
                    "contract": "UNSUPPORTED_FAIL_CLOSED",
                    "family": family,
                    "actual": "RESOLUTION ALLOWED",
                }
            )

    # ======================================================
    # VALID FAMILY WITH NO CONTRACT FAILS CLOSED
    # ======================================================

    try:

        UpstoxInstrumentResolver.resolve_mcx_future(
            family="COPPER",
            candidates=CANDIDATES,
            as_of=AS_OF,
        )

    except UpstoxInstrumentResolutionError:
        pass

    else:

        failures.append(
            {
                "contract": "NO_CONTRACT_FAIL_CLOSED",
                "family": "COPPER",
                "actual": "RESOLUTION ALLOWED",
            }
        )

    # ======================================================
    # RESULT
    # ======================================================

    if failures:

        print(
            "UPSTOX_INSTRUMENT_RESOLVER_CONTRACT: FAIL"
        )

        for failure in failures:

            print(
                "FAIL:",
                failure,
            )

        raise AssertionError(
            "Upstox instrument resolver contract violated"
        )

    print(
        "UPSTOX_INSTRUMENT_RESOLVER_CONTRACT: PASS"
    )

    print(
        "Resolved families:",
        len(EXPECTED_RESOLUTIONS),
    )

    print(
        "Unsupported fail-closed cases:",
        len(FAIL_CLOSED_FAMILIES),
    )

    print(
        "No-contract fail-closed cases: 1"
    )

    print(
        "Network required: NO"
    )


if __name__ == "__main__":
    main()
