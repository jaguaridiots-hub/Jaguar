"""
Jaguar Quant X Enterprise
Upstox Timeframe Adapter v1

Purpose:
Translate Jaguar timeframe identities into the explicit
unit and interval grammar required by Upstox Candle V3.

This module:
- performs no network request
- requires no provider credential
- has no pandas dependency
- has no Upstox SDK dependency
"""


class UpstoxTimeframeError(ValueError):
    """
    Raised when a Jaguar timeframe cannot be represented by
    the supported Upstox Candle V3 contract.
    """


class UpstoxTimeframe:
    """
    Immutable normalized Upstox timeframe value.
    """

    __slots__ = (
        "jaguar",
        "unit",
        "interval",
    )

    def __init__(
        self,
        jaguar,
        unit,
        interval,
    ):
        self.jaguar = jaguar
        self.unit = unit
        self.interval = int(interval)

    def as_tuple(self):
        """
        Return the provider routing tuple.
        """

        return (
            self.unit,
            self.interval,
        )

    def __eq__(self, other):
        if not isinstance(
            other,
            UpstoxTimeframe,
        ):
            return NotImplemented

        return (
            self.jaguar,
            self.unit,
            self.interval,
        ) == (
            other.jaguar,
            other.unit,
            other.interval,
        )

    def __repr__(self):
        return (
            "UpstoxTimeframe("
            f"jaguar={self.jaguar!r}, "
            f"unit={self.unit!r}, "
            f"interval={self.interval!r}"
            ")"
        )


class UpstoxTimeframeAdapter:
    """
    Translate Jaguar timeframe strings into Upstox V3
    candle unit and interval values.
    """

    MINUTE_MIN = 1
    MINUTE_MAX = 300

    HOUR_MIN = 1
    HOUR_MAX = 5

    DAY_INTERVAL = 1
    WEEK_INTERVAL = 1
    MONTH_INTERVAL = 1

    @staticmethod
    def _normalize(timeframe):
        """
        Normalize the external Jaguar timeframe identity.
        """

        if not isinstance(
            timeframe,
            str,
        ):
            return None

        normalized = (
            timeframe
            .strip()
            .lower()
        )

        if not normalized:
            return None

        return normalized

    @classmethod
    def parse(cls, timeframe):
        """
        Parse a Jaguar timeframe into the Upstox V3 grammar.

        Supported Jaguar forms:
        - 1m through 300m
        - 1h through 5h
        - 1d
        - 1w
        - 1mo

        Unsupported values fail closed.
        """

        normalized = cls._normalize(
            timeframe
        )

        if normalized is None:

            raise UpstoxTimeframeError(
                "Unsupported Jaguar timeframe: "
                f"{timeframe!r}"
            )

        # ==================================================
        # MONTHS
        # ==================================================

        if normalized.endswith("mo"):

            amount_text = normalized[:-2]

            if amount_text.isdigit():

                amount = int(amount_text)

                if amount == cls.MONTH_INTERVAL:

                    return UpstoxTimeframe(
                        jaguar=normalized,
                        unit="months",
                        interval=amount,
                    )

        # ==================================================
        # MINUTES / HOURS / DAYS / WEEKS
        # ==================================================

        suffix = normalized[-1]
        amount_text = normalized[:-1]

        if not amount_text.isdigit():

            raise UpstoxTimeframeError(
                "Unsupported Jaguar timeframe: "
                f"{timeframe!r}"
            )

        amount = int(amount_text)

        if suffix == "m":

            if (
                cls.MINUTE_MIN
                <= amount
                <= cls.MINUTE_MAX
            ):

                return UpstoxTimeframe(
                    jaguar=normalized,
                    unit="minutes",
                    interval=amount,
                )

        elif suffix == "h":

            if (
                cls.HOUR_MIN
                <= amount
                <= cls.HOUR_MAX
            ):

                return UpstoxTimeframe(
                    jaguar=normalized,
                    unit="hours",
                    interval=amount,
                )

        elif suffix == "d":

            if amount == cls.DAY_INTERVAL:

                return UpstoxTimeframe(
                    jaguar=normalized,
                    unit="days",
                    interval=amount,
                )

        elif suffix == "w":

            if amount == cls.WEEK_INTERVAL:

                return UpstoxTimeframe(
                    jaguar=normalized,
                    unit="weeks",
                    interval=amount,
                )

        raise UpstoxTimeframeError(
            "Unsupported Jaguar timeframe: "
            f"{timeframe!r}"
        )
