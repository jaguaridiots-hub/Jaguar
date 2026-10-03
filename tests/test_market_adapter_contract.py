"""
Jaguar Quant X Enterprise
Market Adapter Routing Contract v1

Purpose:
Prove that MarketAdapter preserves deterministic market
identity and fails closed before provider routing.

This contract does not execute provider network requests.
"""

from market.adapter import MarketAdapter


# ==========================================================
# MARKET IDENTITY DELEGATION
# ==========================================================

EXPECTED_MARKETS = {
    "BTCUSDT": "CRYPTO",
    "RELIANCE.NS": "NSE",
    "SBIN.BO": "BSE",
    "GOLD": "MCX",
    "GOLDM": "MCX",
    "SILVER": "MCX",
    "SILVERM": "MCX",
    "CRUDEOIL": "MCX",
    "CRUDEOILM": "MCX",
    "NATURALGAS": "MCX",
    "NATGASMINI": "MCX",
    "XAUUSD": "FOREX",
    "XAGUSD": "FOREX",
    "EURUSD": "FOREX",
    "AAPL": "US",
    "SPY": "US",
}


# ==========================================================
# FAIL-CLOSED INPUTS
# ==========================================================

UNKNOWN_SYMBOLS = (
    "UNKNOWN123",
    "JAGUAR",
    "RELIANCE",
    "",
    None,
)


def main():

    failures = []

    # ======================================================
    # DETECTOR DELEGATION CONTRACT
    # ======================================================

    for symbol, expected in (
        EXPECTED_MARKETS.items()
    ):

        actual = MarketAdapter.get_market(
            symbol
        )

        if actual != expected:

            failures.append(
                {
                    "contract": "MARKET_IDENTITY",
                    "symbol": symbol,
                    "expected": expected,
                    "actual": actual,
                }
            )

    # ======================================================
    # FAIL-CLOSED LOAD CONTRACT
    # ======================================================

    for symbol in UNKNOWN_SYMBOLS:

        try:

            MarketAdapter.load(
                symbol
            )

        except Exception as exc:

            message = str(exc)

            if "Unsupported Market : UNKNOWN" not in message:

                failures.append(
                    {
                        "contract": "FAIL_CLOSED_MESSAGE",
                        "symbol": symbol,
                        "actual": message,
                    }
                )

        else:

            failures.append(
                {
                    "contract": "FAIL_CLOSED_LOAD",
                    "symbol": symbol,
                    "actual": "PROVIDER LOAD ALLOWED",
                }
            )

    # ======================================================
    # RESULT
    # ======================================================

    if failures:

        print(
            "MARKET_ADAPTER_CONTRACT: FAIL"
        )

        for failure in failures:

            print(
                "FAIL:",
                failure,
            )

        raise AssertionError(
            "Market adapter contract violated"
        )

    print(
        "MARKET_ADAPTER_CONTRACT: PASS"
    )

    print(
        "Identity cases:",
        len(EXPECTED_MARKETS),
    )

    print(
        "Fail-closed cases:",
        len(UNKNOWN_SYMBOLS),
    )


if __name__ == "__main__":
    main()
