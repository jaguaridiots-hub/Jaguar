"""Read-only Upstox account funds and margin model."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import isfinite
from typing import Any

from market.upstox_order_transport import (
    UpstoxOrderTransport,
    UpstoxOrderTransportError,
)


class AccountReadModelError(RuntimeError):
    """Raised when the broker account read model is unavailable."""


@dataclass(frozen=True)
class AccountSnapshot:
    authority: str
    status: str
    available_margin: float | None
    used_margin: float | None
    payin_amount: float | None
    notional_cash: float | None
    segment: str | None
    freshness: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _number(
    value: Any,
    field_name: str,
) -> float | None:
    if value is None:
        return None

    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise AccountReadModelError(
            f"Invalid Upstox account field: {field_name}"
        ) from exc

    if not isfinite(result):
        raise AccountReadModelError(
            f"Invalid Upstox account field: {field_name}"
        )

    return result


def _mapping(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise AccountReadModelError(
            "Upstox funds response must be an object"
        )

    status = str(value.get("status", "")).strip().lower()
    if status and status != "success":
        raise AccountReadModelError(
            "Upstox funds response was not successful"
        )

    data = value.get("data")

    if not isinstance(data, dict):
        raise AccountReadModelError(
            "Upstox funds response data must be an object"
        )

    equity = data.get("equity")

    if isinstance(equity, dict):
        return equity

    return data


def build_account_snapshot(
    *,
    transport: UpstoxOrderTransport | None = None,
    segment: str | None = None,
) -> dict[str, Any]:
    """Return one strictly read-only broker account observation."""

    if transport is None:
        transport = UpstoxOrderTransport()

    try:
        response = transport.get_funds_and_margin(
            segment=segment
        )
        data = _mapping(response)

        return AccountSnapshot(
            authority="UPSTOX_FUND_AND_MARGIN_API",
            status="AVAILABLE",
            available_margin=_number(
                data.get("available_margin"),
                "available_margin",
            ),
            used_margin=_number(
                data.get("used_margin"),
                "used_margin",
            ),
            payin_amount=_number(
                data.get("payin_amount"),
                "payin_amount",
            ),
            notional_cash=_number(
                data.get("notional_cash"),
                "notional_cash",
            ),
            segment=(
                str(segment).strip().upper()
                if segment is not None
                else None
            ),
            freshness="CURRENT",
        ).to_dict()

    except UpstoxOrderTransportError as exc:
        raise AccountReadModelError(
            "Upstox account funds read failed"
        ) from exc
    except AccountReadModelError:
        raise
    except Exception as exc:
        raise AccountReadModelError(
            "Account read model unavailable"
        ) from exc
