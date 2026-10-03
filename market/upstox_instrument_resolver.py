"""
Jaguar Quant X Enterprise
Upstox Instrument Resolver v1

Purpose:
Resolve Jaguar instrument identities from Upstox instrument
candidate records.

The resolver is deliberately transport-independent.

It does not:
- execute network requests
- read provider credentials
- depend on pandas
- depend on the Upstox SDK
- guess an instrument key

Commodity family aliases resolve to the nearest valid MCX
futures contract by expiry.
"""

from datetime import date, datetime


class UpstoxInstrumentResolutionError(
    RuntimeError
):
    """
    Raised when an instrument cannot be resolved safely.
    """


class UpstoxInstrumentResolver:
    """
    Deterministic resolver for Upstox instrument records.
    """

    MCX_FAMILIES = {
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

    @staticmethod
    def _text(value):
        """
        Normalize text for deterministic comparison.
        """

        if value is None:
            return ""

        return str(value).strip().upper()

    @classmethod
    def _instrument_key(cls, record):
        """
        Read the canonical Upstox instrument identity.
        """

        return str(
            record.get(
                "instrument_key",
                "",
            )
            or ""
        ).strip()

    @classmethod
    def _trading_symbol(cls, record):
        """
        Read the provider trading symbol.
        """

        return cls._text(
            record.get("trading_symbol")
            or record.get("tradingsymbol")
            or record.get("symbol")
        )

    @classmethod
    def _exchange(cls, record):
        return cls._text(
            record.get("exchange")
        )

    @classmethod
    def _segment(cls, record):
        return cls._text(
            record.get("segment")
        )

    @classmethod
    def _instrument_type(cls, record):
        return cls._text(
            record.get("instrument_type")
            or record.get("instrumentType")
        )

    @staticmethod
    def _expiry(record):
        """
        Normalize supported Upstox expiry representations.

        Returns datetime.date or None.
        """

        value = record.get("expiry")

        if value is None:
            return None

        if isinstance(value, datetime):
            return value.date()

        if isinstance(value, date):
            return value

        if isinstance(value, (int, float)):

            timestamp = float(value)

            if timestamp > 10_000_000_000:
                timestamp /= 1000.0

            try:
                return datetime.utcfromtimestamp(
                    timestamp
                ).date()

            except (
                OverflowError,
                OSError,
                ValueError,
            ):
                return None

        text = str(value).strip()

        if not text:
            return None

        for format_string in (
            "%Y-%m-%d",
            "%d-%m-%Y",
            "%d/%m/%Y",
        ):

            try:

                return datetime.strptime(
                    text,
                    format_string,
                ).date()

            except ValueError:
                pass

        return None

    @classmethod
    def _is_future(cls, record):
        """
        Identify futures without relying on one spelling only.
        """

        instrument_type = (
            cls._instrument_type(record)
        )

        return instrument_type in {
            "FUT",
            "FUTURE",
            "FUTURES",
        }

    @classmethod
    def _matches_family(
        cls,
        record,
        family,
    ):
        """
        Match a contract to one Jaguar commodity family.

        Exact family-prefix matching prevents GOLD from
        accidentally consuming GOLDM contracts.
        """

        trading_symbol = (
            cls._trading_symbol(record)
        )

        if not trading_symbol:
            return False

        if not trading_symbol.startswith(family):
            return False

        suffix = trading_symbol[
            len(family):
        ]

        if not suffix:
            return True

        first_character = suffix[0]

        return not first_character.isalpha()

    @classmethod
    def resolve_mcx_future(
        cls,
        family,
        candidates,
        as_of=None,
    ):
        """
        Resolve the nearest valid MCX futures contract.

        Resolution invariants:
        - supported Jaguar commodity family
        - MCX exchange
        - MCX_FO segment
        - futures instrument
        - exact commodity family
        - valid instrument_key
        - valid expiry
        - expiry on or after as_of
        - earliest valid expiry wins
        """

        normalized_family = cls._text(
            family
        )

        if (
            normalized_family
            not in cls.MCX_FAMILIES
        ):

            raise UpstoxInstrumentResolutionError(
                "Unsupported MCX commodity family: "
                f"{family!r}"
            )

        if as_of is None:
            as_of = date.today()

        elif isinstance(as_of, datetime):
            as_of = as_of.date()

        elif not isinstance(as_of, date):

            raise UpstoxInstrumentResolutionError(
                "Invalid resolver as_of date: "
                f"{as_of!r}"
            )

        if not isinstance(
            candidates,
            (list, tuple),
        ):

            raise UpstoxInstrumentResolutionError(
                "Instrument candidates must be "
                "a list or tuple"
            )

        eligible = []

        for record in candidates:

            if not isinstance(record, dict):
                continue

            if cls._exchange(record) != "MCX":
                continue

            if cls._segment(record) != "MCX_FO":
                continue

            if not cls._is_future(record):
                continue

            if not cls._matches_family(
                record,
                normalized_family,
            ):
                continue

            instrument_key = (
                cls._instrument_key(record)
            )

            if not instrument_key:
                continue

            expiry = cls._expiry(record)

            if expiry is None:
                continue

            if expiry < as_of:
                continue

            eligible.append(
                (
                    expiry,
                    instrument_key,
                    record,
                )
            )

        if not eligible:

            raise UpstoxInstrumentResolutionError(
                "No valid Upstox MCX futures contract "
                "resolved for commodity family: "
                f"{normalized_family}"
            )

        eligible.sort(
            key=lambda item: (
                item[0],
                item[1],
            )
        )

        return eligible[0][2]
