"""Read-only broker position projection from Upstox."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import isfinite
from typing import Any

from intelligence.live_broker_adapter import (
    LiveBrokerAdapter,
    LiveBrokerAdapterError,
)


class BrokerPositionReadModelError(RuntimeError):
    """Raised when broker position state cannot be trusted."""


@dataclass(frozen=True)
class BrokerPosition:
    instrument_token: str
    broker_symbol: str | None
    quantity: float
    average_price: float | None
    pnl: float | None
    unrealised_pnl: float | None
    realised_pnl: float | None
    last_price: float | None
    value: float | None
    exchange: str | None
    product: str | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BrokerPositionSnapshot:
    authority: str
    status: str
    positions: tuple[BrokerPosition, ...]
    freshness: str
    quantity_source: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "authority": self.authority,
            "status": self.status,
            "positions": [
                position.to_dict()
                for position in self.positions
            ],
            "freshness": self.freshness,
            "quantity_source": self.quantity_source,
        }


def _text(value: Any) -> str | None:
    if value is None:
        return None

    value = str(value).strip()
    return value if value else None


def _number(
    value: Any,
    field_name: str,
    *,
    allow_none: bool = True,
) -> float | None:
    if value is None:
        if allow_none:
            return None
        raise BrokerPositionReadModelError(
            f"Missing broker position field: {field_name}"
        )

    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise BrokerPositionReadModelError(
            f"Invalid broker position field: {field_name}"
        ) from exc

    if not isfinite(result):
        raise BrokerPositionReadModelError(
            f"Invalid broker position field: {field_name}"
        )

    return result


def _normalize(position: Any) -> BrokerPosition:
    if not isinstance(position, dict):
        raise BrokerPositionReadModelError(
            "Broker position must be an object"
        )

    instrument_token = _text(
        position.get("instrument_token")
    )

    if not instrument_token:
        raise BrokerPositionReadModelError(
            "Broker position instrument_token is missing"
        )

    quantity = _number(
        position.get("quantity"),
        "quantity",
        allow_none=False,
    )

    if quantity < 0:
        raise BrokerPositionReadModelError(
            "Broker position quantity cannot be negative"
        )

    return BrokerPosition(
        instrument_token=instrument_token,
        broker_symbol=_text(
            position.get("trading_symbol")
            or position.get("tradingsymbol")
        ),
        quantity=quantity,
        average_price=_number(
            position.get("average_price"),
            "average_price",
        ),
        pnl=_number(
            position.get("pnl"),
            "pnl",
        ),
        unrealised_pnl=_number(
            position.get("unrealised"),
            "unrealised",
        ),
        realised_pnl=_number(
            position.get("realised"),
            "realised",
        ),
        last_price=_number(
            position.get("last_price"),
            "last_price",
        ),
        value=_number(
            position.get("value"),
            "value",
        ),
        exchange=_text(position.get("exchange")),
        product=_text(position.get("product")),
    )


def build_broker_position_snapshot(
    *,
    adapter: LiveBrokerAdapter | None = None,
) -> dict[str, Any]:
    """Return one strictly read-only broker position observation."""

    if adapter is None:
        adapter = LiveBrokerAdapter()

    try:
        raw_positions = adapter.get_positions()

        if not isinstance(raw_positions, list):
            raise BrokerPositionReadModelError(
                "Broker positions must be a list"
            )

        normalized = []

        for raw_position in raw_positions:
            position = _normalize(raw_position)

            # Upstox can return records whose current quantity is zero.
            # Those are not open portfolio positions.
            if abs(position.quantity) <= 1e-12:
                continue

            normalized.append(position)

        normalized.sort(
            key=lambda position: position.instrument_token
        )

        return BrokerPositionSnapshot(
            authority="UPSTOX_SHORT_TERM_POSITIONS",
            status="AVAILABLE",
            positions=tuple(normalized),
            freshness="CURRENT",
            quantity_source="UPSTOX_POSITION_API",
        ).to_dict()

    except LiveBrokerAdapterError as exc:
        raise BrokerPositionReadModelError(
            "Upstox broker position read failed"
        ) from exc
    except BrokerPositionReadModelError:
        raise
    except Exception as exc:
        raise BrokerPositionReadModelError(
            "Broker position read model unavailable"
        ) from exc
