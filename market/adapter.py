from core.market_detector import MarketDetector

class MarketAdapter:

    @staticmethod
    def get_market(symbol):
        return MarketDetector.detect(symbol)

    @staticmethod
    def load(
        symbol,
        interval=None,
        limit=None,
        *,
        intraday=None,
    ):
        market = MarketDetector.detect(symbol)

        if (
            interval is not None
            or limit is not None
            or intraday is not None
        ):
            from market.provider import (
                MarketProvider,
            )

            provider_interval = (
                "15m"
                if interval is None
                else interval
            )
            provider_limit = (
                500
                if limit is None
                else limit
            )

            return MarketProvider.load(
                symbol,
                provider_interval,
                provider_limit,
                intraday=intraday,
            )

        if market == "CRYPTO":
            from market.crypto import get_data

        elif market == "NSE":
            from market.nse import get_data

        elif market == "BSE":
            from market.bse import get_data

        elif market == "FOREX":
            from market.forex import get_data

        elif market == "US":
            from market.us import get_data

        elif market == "MCX":
            from market.mcx import get_data

        else:
            raise Exception(
                f"Unsupported Market : {market}"
            )

        return get_data(symbol)

# ==========================================
# Legacy Compatibility Functions
# ==========================================

def detect_market(symbol):
    return MarketAdapter.get_market(symbol)


def load_market(symbol):
    return MarketAdapter.load(symbol)
