"""Read-only Upstox Fund & Margin V3 account model."""

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
    available_to_trade: float | None
    cash_available_to_trade: float | None
    pledge_available_to_trade: float | None
    cash_margin_used: float | None
    pledge_margin_used: float | None
    unsettled_profit_today: float | None
    unsettled_profit_previous_days: float | None
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
            "Upstox funds V3 response must be an object"
        )

    status = str(value.get("status", "")).strip().lower()

    if status != "success":
        raise AccountReadModelError(
            "Upstox funds V3 response was not successful"
        )

    data = value.get("data")

    if not isinstance(data, dict):
        raise AccountReadModelError(
            "Upstox funds V3 response data must be an object"
        )

    available = data.get("available_to_trade")
    unavailable = data.get("unavailable_to_trade")

    if not isinstance(available, dict):
        raise AccountReadModelError(
            "Upstox funds V3 available_to_trade is unavailable"
        )

    if not isinstance(unavailable, dict):
        raise AccountReadModelError(
            "Upstox funds V3 unavailable_to_trade is unavailable"
        )

    return data


def build_account_snapshot(
    *,
    transport: UpstoxOrderTransport | None = None,
) -> dict[str, Any]:
    """Return one strictly read-only Upstox Fund & Margin V3 observation."""

    if transport is None:
        transport = UpstoxOrderTransport()

    try:
        response = transport.get_funds_and_margin_v3()
        data = _mapping(response)

        available = data["available_to_trade"]
        cash = available.get("cash_available_to_trade")
        pledge = available.get("pledge_available_to_trade")

        if not isinstance(cash, dict):
            raise AccountReadModelError(
                "Upstox funds V3 cash_available_to_trade is unavailable"
            )

        if not isinstance(pledge, dict):
            raise AccountReadModelError(
                "Upstox funds V3 pledge_available_to_trade is unavailable"
            )

        cash_margin = cash.get("margin_used")
        pledge_margin = pledge.get("margin_used")

        if not isinstance(cash_margin, dict):
            raise AccountReadModelError(
                "Upstox funds V3 cash margin_used is unavailable"
            )

        if not isinstance(pledge_margin, dict):
            raise AccountReadModelError(
                "Upstox funds V3 pledge margin_used is unavailable"
            )

        unavailable_cash = data[
            "unavailable_to_trade"
        ].get("cash_unavailable_to_trade")

        if not isinstance(unavailable_cash, dict):
            raise AccountReadModelError(
                "Upstox funds V3 cash_unavailable_to_trade is unavailable"
            )

        unsettled = unavailable_cash.get("unsettled_profit")

        if not isinstance(unsettled, dict):
            raise AccountReadModelError(
                "Upstox funds V3 unsettled_profit is unavailable"
            )

        return AccountSnapshot(
            authority="UPSTOX_FUND_AND_MARGIN_V3",
            status="AVAILABLE",
            available_to_trade=_number(
                available.get("total"),
                "available_to_trade.total",
            ),
            cash_available_to_trade=_number(
                cash.get("total"),
                "cash_available_to_trade.total",
            ),
            pledge_available_to_trade=_number(
                pledge.get("total"),
                "pledge_available_to_trade.total",
            ),
            cash_margin_used=_number(
                cash_margin.get("total"),
                "cash_available_to_trade.margin_used.total",
            ),
            pledge_margin_used=_number(
                pledge_margin.get("total"),
                "pledge_available_to_trade.margin_used.total",
            ),
            unsettled_profit_today=_number(
                unsettled.get("todays_profit"),
                "cash_unavailable_to_trade.unsettled_profit.todays_profit",
            ),
            unsettled_profit_previous_days=_number(
                unsettled.get("previous_days"),
                "cash_unavailable_to_trade.unsettled_profit.previous_days",
            ),
            freshness="CURRENT",
        ).to_dict()

    except UpstoxOrderTransportError as exc:
        raise AccountReadModelError(
            "Upstox account funds V3 read failed"
        ) from exc
    except AccountReadModelError:
        raise
    except Exception as exc:
        raise AccountReadModelError(
            "Account read model unavailable"
        ) from exc
