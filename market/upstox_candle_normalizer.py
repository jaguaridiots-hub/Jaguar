"""
Jaguar Quant X Enterprise
Upstox Candle Normalizer v1

Purpose:
Normalize Upstox candle responses into Jaguar's canonical
seven-field candle contract.

Canonical Jaguar candle:

{
    "time": int,
    "close_time": int,
    "open": float,
    "high": float,
    "low": float,
    "close": float,
    "volume": float,
}

Provider open interest is intentionally excluded from the
canonical candle contract.

No network request is executed.
No pandas dependency is required.
"""

from datetime import datetime


class UpstoxCandleNormalizationError(
    RuntimeError
):
    """
    Raised when an Upstox candle payload cannot be normalized
    safely into the Jaguar candle contract.
    """


class UpstoxCandleNormalizer:
    """
    Normalize Upstox candle arrays into canonical Jaguar
    candle dictionaries.
    """

    CANONICAL_FIELDS = (
        "time",
        "close_time",
        "open",
        "high",
        "low",
        "close",
        "volume",
    )

    FIXED_UNIT_MILLISECONDS = {
        "minutes": 60 * 1000,
        "hours": 60 * 60 * 1000,
        "days": 24 * 60 * 60 * 1000,
        "weeks": 7 * 24 * 60 * 60 * 1000,
    }

    @staticmethod
    def _timestamp_milliseconds(value):
        """
        Normalize an Upstox ISO timestamp into Unix epoch
        milliseconds.

        Timezone-aware provider timestamps preserve their
        absolute instant.
        """

        if not isinstance(value, str):

            raise UpstoxCandleNormalizationError(
                "Upstox candle timestamp must be a string"
            )

        text = value.strip()

        if not text:

            raise UpstoxCandleNormalizationError(
                "Upstox candle timestamp is unavailable"
            )

        if text.endswith("Z"):
            text = (
                text[:-1]
                + "+00:00"
            )

        try:

            parsed = datetime.fromisoformat(
                text
            )

        except ValueError as exc:

            raise UpstoxCandleNormalizationError(
                "Invalid Upstox candle timestamp: "
                f"{value!r}"
            ) from exc

        if parsed.tzinfo is None:

            raise UpstoxCandleNormalizationError(
                "Upstox candle timestamp must include "
                "timezone information"
            )

        return int(
            parsed.timestamp()
            * 1000
        )

    @classmethod
    def _duration_milliseconds(
        cls,
        timeframe,
    ):
        """
        Return fixed candle duration in milliseconds.

        Calendar months are intentionally rejected because
        their duration is not fixed.
        """

        unit = str(
            getattr(
                timeframe,
                "unit",
                "",
            )
            or ""
        ).strip().lower()

        try:

            interval = int(
                getattr(
                    timeframe,
                    "interval",
                    0,
                )
            )

        except (TypeError, ValueError) as exc:

            raise UpstoxCandleNormalizationError(
                "Invalid normalized candle interval"
            ) from exc

        if interval <= 0:

            raise UpstoxCandleNormalizationError(
                "Normalized candle interval must be positive"
            )

        unit_milliseconds = (
            cls.FIXED_UNIT_MILLISECONDS.get(
                unit
            )
        )

        if unit_milliseconds is None:

            raise UpstoxCandleNormalizationError(
                "Unsupported fixed-duration candle unit: "
                f"{unit!r}"
            )

        return (
            unit_milliseconds
            * interval
        )

    @staticmethod
    def _number(
        value,
        field,
    ):
        """
        Normalize one numeric candle field.
        """

        try:

            return float(value)

        except (TypeError, ValueError) as exc:

            raise UpstoxCandleNormalizationError(
                "Invalid Upstox candle numeric field "
                f"{field}: {value!r}"
            ) from exc

    @classmethod
    def normalize_candle(
        cls,
        raw_candle,
        timeframe,
    ):
        """
        Normalize one Upstox candle array.

        Expected provider positions:
        0 timestamp
        1 open
        2 high
        3 low
        4 close
        5 volume
        6 open interest, optional for Jaguar
        """

        if not isinstance(
            raw_candle,
            (list, tuple),
        ):

            raise UpstoxCandleNormalizationError(
                "Upstox candle must be a list or tuple"
            )

        if len(raw_candle) < 6:

            raise UpstoxCandleNormalizationError(
                "Upstox candle has insufficient fields"
            )

        open_time = (
            cls._timestamp_milliseconds(
                raw_candle[0]
            )
        )

        duration = (
            cls._duration_milliseconds(
                timeframe
            )
        )

        close_time = (
            open_time
            + duration
            - 1
        )

        candle = {
            "time": open_time,
            "close_time": close_time,
            "open": cls._number(
                raw_candle[1],
                "open",
            ),
            "high": cls._number(
                raw_candle[2],
                "high",
            ),
            "low": cls._number(
                raw_candle[3],
                "low",
            ),
            "close": cls._number(
                raw_candle[4],
                "close",
            ),
            "volume": cls._number(
                raw_candle[5],
                "volume",
            ),
        }

        if tuple(candle.keys()) != (
            cls.CANONICAL_FIELDS
        ):

            raise UpstoxCandleNormalizationError(
                "Canonical Jaguar candle field contract "
                "was not preserved"
            )

        return candle

    @classmethod
    def normalize_payload(
        cls,
        payload,
        timeframe,
    ):
        """
        Normalize an Upstox candle API payload.

        Output is sorted by canonical open time and duplicate
        candle identities fail closed.
        """

        if not isinstance(payload, dict):

            raise UpstoxCandleNormalizationError(
                "Upstox candle payload must be an object"
            )

        data = payload.get("data")

        if not isinstance(data, dict):

            raise UpstoxCandleNormalizationError(
                "Upstox candle payload data is unavailable"
            )

        raw_candles = data.get("candles")

        if not isinstance(raw_candles, list):

            raise UpstoxCandleNormalizationError(
                "Upstox candle collection is unavailable"
            )

        candles = [
            cls.normalize_candle(
                raw_candle,
                timeframe,
            )
            for raw_candle in raw_candles
        ]

        candles.sort(
            key=lambda candle: candle["time"]
        )

        seen_times = set()

        for candle in candles:

            candle_time = candle["time"]

            if candle_time in seen_times:

                raise UpstoxCandleNormalizationError(
                    "Duplicate canonical candle identity: "
                    f"{candle_time}"
                )

            seen_times.add(
                candle_time
            )

        return candles
