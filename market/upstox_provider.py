"""
Jaguar Quant X Enterprise
Upstox Market Data Provider v1

Purpose:
Orchestrate the proven Upstox market-data components into
one canonical Jaguar candle provider.

Current provider scope:
- MCX commodity futures families

Pipeline:
Jaguar commodity family
    -> timeframe adapter
    -> instrument search
    -> MCX futures resolver
    -> Upstox candle transport
    -> canonical candle normalizer
    -> canonical limit

This provider does not:
- duplicate transport logic
- duplicate timeframe mapping
- duplicate instrument resolution
- duplicate candle normalization
- depend on pandas
- depend on yfinance
- execute requests at import time
"""

from datetime import date, datetime

from market.upstox_candle_normalizer import (
    UpstoxCandleNormalizationError,
    UpstoxCandleNormalizer,
)
from market.upstox_instrument_resolver import (
    UpstoxInstrumentResolutionError,
    UpstoxInstrumentResolver,
)
from market.upstox_timeframe import (
    UpstoxTimeframeAdapter,
)
from market.upstox_transport import (
    UpstoxTransport,
    UpstoxTransportError,
)


class UpstoxProviderError(RuntimeError):
    """
    Raised when Upstox provider orchestration fails.
    """


class UpstoxProvider:
    """
    Canonical Jaguar provider for Upstox-backed instruments.
    """

    DEFAULT_LIMIT = 300

    def __init__(
        self,
        transport=None,
    ):
        self._transport = (
            transport
            if transport is not None
            else UpstoxTransport()
        )

    @staticmethod
    def _normalize_limit(limit):
        """
        Validate the canonical Jaguar candle limit.
        """

        if isinstance(limit, bool):

            raise UpstoxProviderError(
                "Candle limit must be a positive integer"
            )

        try:

            normalized = int(limit)

        except (TypeError, ValueError) as exc:

            raise UpstoxProviderError(
                "Invalid candle limit: "
                f"{limit!r}"
            ) from exc

        if normalized <= 0:

            raise UpstoxProviderError(
                "Candle limit must be positive"
            )

        return normalized

    @staticmethod
    def _normalize_date(
        value,
        field,
    ):
        """
        Normalize provider request dates to YYYY-MM-DD.
        """

        if isinstance(value, datetime):
            value = value.date()

        if isinstance(value, date):
            return value.isoformat()

        if isinstance(value, str):

            text = value.strip()

            try:

                return date.fromisoformat(
                    text
                ).isoformat()

            except ValueError as exc:

                raise UpstoxProviderError(
                    f"Invalid {field}: {value!r}"
                ) from exc

        raise UpstoxProviderError(
            f"Invalid {field}: {value!r}"
        )

    @staticmethod
    def _extract_search_candidates(
        payload,
    ):
        """
        Extract instrument records from the provider search
        response.

        The provider boundary fails closed on malformed search
        payloads.
        """

        if not isinstance(payload, dict):

            raise UpstoxProviderError(
                "Instrument search payload must be an object"
            )

        data = payload.get("data")

        if isinstance(data, list):
            return data

        if isinstance(data, dict):

            instruments = data.get(
                "instruments"
            )

            if isinstance(instruments, list):
                return instruments

        raise UpstoxProviderError(
            "Instrument search candidates are unavailable"
        )

    def _resolve_mcx_future(
        self,
        family,
        as_of,
    ):
        """
        Search and resolve one MCX futures family.
        """

        search_payload = (
            self._transport.search_instruments(
                query=family,
                exchange="MCX",
                segment="MCX_FO",
                instrument_type="FUT",
            )
        )

        candidates = (
            self._extract_search_candidates(
                search_payload
            )
        )

        return (
            UpstoxInstrumentResolver
            .resolve_mcx_future(
                family=family,
                candidates=candidates,
                as_of=as_of,
            )
        )

    def load_mcx(
        self,
        family,
        interval="15m",
        limit=DEFAULT_LIMIT,
        to_date=None,
        from_date=None,
        as_of=None,
        intraday=False,
    ):
        """
        Load canonical Jaguar candles for one MCX commodity
        futures family.

        Historical mode requires to_date and from_date.

        Intraday mode uses the provider intraday V3 route and
        does not accept historical date boundaries.
        """

        normalized_limit = (
            self._normalize_limit(
                limit
            )
        )

        try:

            timeframe = (
                UpstoxTimeframeAdapter.parse(
                    interval
                )
            )

        except Exception as exc:

            raise UpstoxProviderError(
                "Unable to normalize Upstox timeframe: "
                f"{interval!r}"
            ) from exc

        if as_of is None:

            as_of = date.today()

        elif isinstance(as_of, datetime):

            as_of = as_of.date()

        elif not isinstance(as_of, date):

            raise UpstoxProviderError(
                "Invalid instrument resolution as_of date: "
                f"{as_of!r}"
            )

        try:

            instrument = (
                self._resolve_mcx_future(
                    family=family,
                    as_of=as_of,
                )
            )

            instrument_key = str(
                instrument.get(
                    "instrument_key",
                    "",
                )
                or ""
            ).strip()

            if not instrument_key:

                raise UpstoxProviderError(
                    "Resolved Upstox instrument key "
                    "is unavailable"
                )

            if intraday:

                if (
                    to_date is not None
                    or from_date is not None
                ):

                    raise UpstoxProviderError(
                        "Intraday candle requests do not "
                        "accept historical date boundaries"
                    )

                raw_payload = (
                    self._transport
                    .intraday_candles(
                        instrument_key=instrument_key,
                        unit=timeframe.unit,
                        interval=timeframe.interval,
                    )
                )

            else:

                if (
                    to_date is None
                    or from_date is None
                ):

                    raise UpstoxProviderError(
                        "Historical candle requests require "
                        "to_date and from_date"
                    )

                normalized_to_date = (
                    self._normalize_date(
                        to_date,
                        "to_date",
                    )
                )

                normalized_from_date = (
                    self._normalize_date(
                        from_date,
                        "from_date",
                    )
                )

                if (
                    normalized_from_date
                    > normalized_to_date
                ):

                    raise UpstoxProviderError(
                        "Historical from_date cannot be "
                        "after to_date"
                    )

                raw_payload = (
                    self._transport
                    .historical_candles(
                        instrument_key=instrument_key,
                        unit=timeframe.unit,
                        interval=timeframe.interval,
                        to_date=normalized_to_date,
                        from_date=normalized_from_date,
                    )
                )

            candles = (
                UpstoxCandleNormalizer
                .normalize_payload(
                    raw_payload,
                    timeframe,
                )
            )

        except UpstoxProviderError:
            raise

        except (
            UpstoxInstrumentResolutionError,
            UpstoxTransportError,
            UpstoxCandleNormalizationError,
        ) as exc:

            raise UpstoxProviderError(
                "Upstox MCX candle load failed"
            ) from exc

        if len(candles) > normalized_limit:

            candles = candles[
                -normalized_limit:
            ]

        return candles
