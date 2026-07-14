"""
Jaguar Quant X Enterprise
Market Identity Contract v1

Purpose:
Prove deterministic market classification before provider
routing occurs.

This contract protects:
- Crypto routing
- Legacy NSE / BSE aliases
- MCX commodity families
- Forex and global metal identities
- Explicit US instrument identities
- Fail-closed UNKNOWN behaviour

No provider is loaded.
No network request is executed.
"""

from core.market_detector import MarketDetector


EXPECTED_IDENTITIES = {
    # ======================================================
    # CRYPTO
    # ======================================================
    "BTCUSDT": "CRYPTO",
    "ETHUSDT": "CRYPTO",
    "SOLUSDT": "CRYPTO",
    "BNBUSDT": "CRYPTO",
    "XRPUSDT": "CRYPTO",

    # ======================================================
    # LEGACY INDIA INPUT ALIASES
    # ======================================================
    "RELIANCE.NS": "NSE",
    "TCS.NS": "NSE",
    "SBIN.NS": "NSE",
    "SBIN.BO": "BSE",

    # ======================================================
    # MCX PRECIOUS METALS
    # ======================================================
    "GOLD": "MCX",
    "GOLDM": "MCX",
    "SILVER": "MCX",
    "SILVERM": "MCX",

    # ======================================================
    # MCX ENERGY
    # ======================================================
    "CRUDEOIL": "MCX",
    "CRUDEOILM": "MCX",
    "NATURALGAS": "MCX",
    "NATGASMINI": "MCX",

    # ======================================================
    # MCX BASE METALS
    # ======================================================
    "COPPER": "MCX",
    "ZINC": "MCX",
    "LEAD": "MCX",
    "NICKEL": "MCX",
    "ALUMINIUM": "MCX",

    # ======================================================
    # FOREX / GLOBAL METALS
    # ======================================================
    "EURUSD": "FOREX",
    "GBPUSD": "FOREX",
    "USDJPY": "FOREX",
    "USDCHF": "FOREX",
    "AUDUSD": "FOREX",
    "NZDUSD": "FOREX",
    "USDCAD": "FOREX",
    "XAUUSD": "FOREX",
    "XAGUSD": "FOREX",

    # ======================================================
    # EXPLICIT US UNIVERSE
    # ======================================================
    "AAPL": "US",
    "MSFT": "US",
    "GOOGL": "US",
    "GOOG": "US",
    "AMZN": "US",
    "META": "US",
    "NVDA": "US",
    "TSLA": "US",
    "SPY": "US",
    "QQQ": "US",
    "DIA": "US",
    "IWM": "US",

    # ======================================================
    # FAIL CLOSED
    # ======================================================
    "UNKNOWN123": "UNKNOWN",
    "JAGUAR": "UNKNOWN",
    "RELIANCE": "UNKNOWN",
    "": "UNKNOWN",
    None: "UNKNOWN",
}


def main():

    failures = []

    for symbol, expected in (
        EXPECTED_IDENTITIES.items()
    ):

        actual = MarketDetector.detect(
            symbol
        )

        if actual != expected:

            failures.append(
                {
                    "symbol": symbol,
                    "expected": expected,
                    "actual": actual,
                }
            )

    if failures:

        print(
            "MARKET_IDENTITY_CONTRACT: FAIL"
        )

        for failure in failures:

            print(
                "FAIL:",
                failure,
            )

        raise AssertionError(
            "Market identity contract violated"
        )

    print(
        "MARKET_IDENTITY_CONTRACT: PASS"
    )

    print(
        "Cases:",
        len(EXPECTED_IDENTITIES),
    )


if __name__ == "__main__":
    main()
