"""
Jaguar Quant X Enterprise
Market Identity Detector v1.0

Purpose:
Classify an input symbol into a deterministic Jaguar market
identity before provider routing occurs.

Market identities:
- CRYPTO
- NSE
- BSE
- MCX
- FOREX
- US
- UNKNOWN

Design rules:
- Detection is deterministic.
- Unknown symbols fail closed.
- Yahoo-style .NS / .BO inputs are retained only as legacy
  input aliases.
- MCX commodity families are explicit.
- XAUUSD / XAGUSD remain FOREX identities and are distinct
  from MCX GOLD / SILVER instruments.
- No provider is imported here.
- No network request is executed here.
"""


class MarketDetector:
    """
    Deterministic market identity classifier.
    """

    CRYPTO_QUOTES = (
        "USDT",
    )

    MCX_SYMBOLS = {
        "GOLD",
        "GOLDM",
        "SILVER",
        "SILVERM",
        "CRUDEOIL",
        "CRUDEOILM",
        "NATURALGAS",
        "NATGASMINI",
        "COPPER",
        "ZINC",
        "LEAD",
        "NICKEL",
        "ALUMINIUM",
    }

    FOREX_SYMBOLS = {
        "EURUSD",
        "GBPUSD",
        "USDJPY",
        "USDCHF",
        "AUDUSD",
        "NZDUSD",
        "USDCAD",
        "XAUUSD",
        "XAGUSD",
    }

    US_SYMBOLS = {
        "AAPL",
        "MSFT",
        "GOOGL",
        "GOOG",
        "AMZN",
        "META",
        "NVDA",
        "TSLA",
        "SPY",
        "QQQ",
        "DIA",
        "IWM",
    }

    @staticmethod
    def _normalize(symbol):
        """
        Normalize external symbol input safely.
        """

        if symbol is None:
            return ""

        try:
            return str(symbol).strip().upper()

        except (TypeError, ValueError):
            return ""

    @classmethod
    def detect(cls, symbol):
        """
        Return the canonical Jaguar market identity.
        """

        symbol = cls._normalize(symbol)

        if not symbol:
            return "UNKNOWN"

        # ==================================================
        # LEGACY INDIA INPUT ALIASES
        # ==================================================

        if symbol.endswith(".NS"):
            return "NSE"

        if symbol.endswith(".BO"):
            return "BSE"

        # ==================================================
        # MCX COMMODITY FAMILIES
        # ==================================================

        if symbol in cls.MCX_SYMBOLS:
            return "MCX"

        # ==================================================
        # FOREX / GLOBAL METALS
        # ==================================================

        if symbol in cls.FOREX_SYMBOLS:
            return "FOREX"

        # ==================================================
        # CRYPTO
        # ==================================================

        if symbol.endswith(cls.CRYPTO_QUOTES):
            return "CRYPTO"

        # ==================================================
        # EXPLICIT US UNIVERSE
        # ==================================================

        if symbol in cls.US_SYMBOLS:
            return "US"

        # ==================================================
        # FAIL CLOSED
        # ==================================================

        return "UNKNOWN"


if __name__ == "__main__":

    symbols = [
        "BTCUSDT",
        "RELIANCE.NS",
        "SBIN.BO",
        "GOLD",
        "GOLDM",
        "SILVERM",
        "CRUDEOILM",
        "NATGASMINI",
        "XAUUSD",
        "XAGUSD",
        "EURUSD",
        "AAPL",
        "SPY",
        "UNKNOWN123",
        None,
    ]

    for symbol in symbols:
        print(
            symbol,
            "->",
            MarketDetector.detect(symbol),
        )
