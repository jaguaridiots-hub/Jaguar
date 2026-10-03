"""
Jaguar Quant X Enterprise
Market Provider Gateway v2

Purpose:
Provide the stable canonical candle-loading facade used by
Jaguar runtime consumers.

Routing:
- CRYPTO -> canonical Binance candle provider
- MCX    -> canonical Upstox MCX provider
- NSE    -> fail closed until an equity provider capability exists
- BSE    -> fail closed until an equity provider capability exists
- FOREX  -> fail closed until a forex provider exists
- US     -> fail closed until a US market provider exists
- UNKNOWN -> fail closed

Canonical candle contract:

{
    "time": int,
    "close_time": int,
    "open": float,
    "high": float,
    "low": float,
    "close": float,
    "volume": float,
}

Runtime constraints:
- Termux compatible.
- No pandas dependency.
- No yfinance dependency.
- No network request at module import time.
- Temporal intent is never inferred for Upstox MCX requests.
"""

from core.market_detector import MarketDetector
from market.provider_manager import ProviderManager

class MarketProviderError(RuntimeError):
    """
    Raised when canonical provider routing cannot be completed.
    """


class MarketProvider:
    """
    Stable exchange-aware market-data provider facade.

    The first three positional arguments of load() are preserved
    for existing TradingKernel consumers.
    """

    @staticmethod
    def _reject_crypto_temporal_arguments(
        intraday,
        to_date,
        from_date,
        as_of,
    ):
        """
        Binance canonical routing does not consume Upstox
        temporal controls.
        """

        if (
            intraday is not None
            or to_date is not None
            or from_date is not None
            or as_of is not None
        ):
            raise MarketProviderError(
                "CRYPTO provider does not accept Upstox "
                "temporal routing arguments"
            )

    @staticmethod
    def _load_crypto(
        symbol,
        interval,
        limit,
    ):
        """
        Load canonical Binance candles.
        """

        return ProviderManager.load(
            symbol=symbol,
            interval=interval,
            limit=limit,
        )

    @staticmethod
    def _load_mcx(
        symbol,
        interval,
        limit,
        intraday,
        to_date,
        from_date,
        as_of,
    ):
        """
        Load canonical Upstox MCX candles.

        MCX temporal mode must be explicit. The gateway does not
        infer historical or intraday intent.
        """

        if intraday is None:
            raise MarketProviderError(
                "MCX provider requires explicit intraday mode"
            )

        if not isinstance(intraday, bool):
            raise MarketProviderError(
                "MCX intraday mode must be boolean"
            )

        from market.upstox_provider import (
            UpstoxProvider,
            UpstoxProviderError,
        )

        try:
            provider = UpstoxProvider()

            return provider.load_mcx(
                family=symbol,
                interval=interval,
                limit=limit,
                to_date=to_date,
                from_date=from_date,
                as_of=as_of,
                intraday=intraday,
            )

        except UpstoxProviderError as exc:
            raise MarketProviderError(
                "MCX provider routing failed"
            ) from exc

    @staticmethod
    def _load_nse(
        symbol,
        interval,
        limit,
    ):
        """
        Load canonical NSE equity candles.

        NSE is a market-data capability for dashboard/PAPER
        analysis. It is not an execution-authorized broker source.
        """

        from market.nse_provider import (
            NSEProvider,
            NSEProviderError,
        )

        try:
            provider = NSEProvider()

            return provider.load(
                symbol=symbol,
                interval=interval,
                limit=limit,
            )

        except NSEProviderError as exc:
            raise MarketProviderError(
                "NSE provider routing failed"
            ) from exc

    @staticmethod
    def load_with_identity(
        symbol,
        interval="15m",
        limit=500,
        *,
        intraday=None,
        to_date=None,
        from_date=None,
        as_of=None,
    ):
        """
        Load canonical MCX candles together with the exact
        resolver-selected Upstox instrument identity.
        """

        market = MarketDetector.detect(symbol)

        if market != "MCX":
            raise MarketProviderError(
                "Identity-aware loading is currently "
                "supported only for MCX"
            )

        if intraday is None:
            raise MarketProviderError(
                "MCX provider requires explicit intraday mode"
            )

        if not isinstance(intraday, bool):
            raise MarketProviderError(
                "MCX intraday mode must be boolean"
            )

        from market.upstox_provider import (
            UpstoxProvider,
            UpstoxProviderError,
        )

        try:
            provider = UpstoxProvider()

            return provider.load_mcx(
                family=symbol,
                interval=interval,
                limit=limit,
                to_date=to_date,
                from_date=from_date,
                as_of=as_of,
                intraday=intraday,
                include_identity=True,
            )

        except UpstoxProviderError as exc:
            raise MarketProviderError(
                "MCX provider routing failed"
            ) from exc

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
        """
        Load canonical Jaguar candles for one market symbol.

        Existing CRYPTO callers may continue using:

            MarketProvider.load(symbol, interval, limit)

        MCX callers must explicitly declare temporal intent:

            intraday=True

        or:

            intraday=False,
            to_date=...,
            from_date=...

        Unsupported provider capabilities fail closed.
        """

        market = MarketDetector.detect(
            symbol
        )

        if market == "CRYPTO":

            MarketProvider._reject_crypto_temporal_arguments(
                intraday=intraday,
                to_date=to_date,
                from_date=from_date,
                as_of=as_of,
            )

            return ProviderManager.load(
                symbol=symbol,
                interval=interval,
                limit=limit,
            )
        if market == "MCX":

            return MarketProvider._load_mcx(
                symbol=symbol,
                interval=interval,
                limit=limit,
                intraday=intraday,
                to_date=to_date,
                from_date=from_date,
                as_of=as_of,
            )

        if market == "NSE":
            return MarketProvider._load_nse(
                symbol=symbol,
                interval=interval,
                limit=limit,
            )

        if market == "BSE":
            raise MarketProviderError(
                "BSE provider capability is not implemented"
            )

        if market == "FOREX":
            raise MarketProviderError(
                "FOREX provider capability is not implemented"
            )

        if market == "US":
            raise MarketProviderError(
                "US provider capability is not implemented"
            )

        if market == "UNKNOWN":
            raise MarketProviderError(
                f"Unknown market identity for symbol: {symbol!r}"
            )

        raise MarketProviderError(
            f"Unsupported market identity: {market!r}"
        )
