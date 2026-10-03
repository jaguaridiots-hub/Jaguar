"""Read-only canonical portfolio composition and reconciliation."""

from __future__ import annotations

from math import isfinite
from typing import Any

from core.account_read_model import (
    AccountReadModelError,
    build_account_snapshot,
)
from core.broker_position_read_model import (
    BrokerPositionReadModelError,
    build_broker_position_snapshot,
)
from core.portfolio_read_model import (
    PortfolioReadModelError,
    build_portfolio_snapshot,
)


class CanonicalPortfolioReadModelError(RuntimeError):
    """Raised when canonical portfolio state cannot be trusted."""


def _finite_number(value: Any, field: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise CanonicalPortfolioReadModelError(
            f"Invalid {field}"
        ) from exc

    if not isfinite(result):
        raise CanonicalPortfolioReadModelError(
            f"Invalid {field}"
        )

    return result


def _reconcile(
    jaguar_positions: list[dict[str, Any]],
    broker_positions: list[dict[str, Any]],
) -> dict[str, Any]:

    jaguar_by_token = {}
    for position in jaguar_positions:
        token = str(
            position.get("instrument_token") or ""
        ).strip()

        if not token:
            raise CanonicalPortfolioReadModelError(
                "Jaguar position has no instrument identity"
            )

        if token in jaguar_by_token:
            raise CanonicalPortfolioReadModelError(
                f"Duplicate Jaguar instrument identity: {token}"
            )

        jaguar_by_token[token] = position

    broker_by_token = {}
    for position in broker_positions:
        token = str(
            position.get("instrument_token") or ""
        ).strip()

        if not token:
            raise CanonicalPortfolioReadModelError(
                "Broker position has no instrument identity"
            )

        if token in broker_by_token:
            raise CanonicalPortfolioReadModelError(
                f"Duplicate broker instrument identity: {token}"
            )

        broker_by_token[token] = position

    matches = []
    mismatches = []
    unmatched_broker = []

    for token, jaguar in jaguar_by_token.items():
        broker = broker_by_token.get(token)

        if broker is None:
            mismatches.append({
                "instrument_token": token,
                "status": "NO_BROKER_POSITION",
                "jaguar_quantity": jaguar.get("quantity"),
                "broker_quantity": None,
            })
            continue

        jaguar_quantity = _finite_number(
            jaguar.get("quantity"),
            "Jaguar quantity",
        )
        broker_quantity = _finite_number(
            broker.get("quantity"),
            "broker quantity",
        )

        quantity_match = (
            abs(jaguar_quantity - broker_quantity) <= 1e-12
        )

        if quantity_match:
            matches.append({
                "instrument_token": token,
                "jaguar_quantity": jaguar_quantity,
                "broker_quantity": broker_quantity,
            })
        else:
            mismatches.append({
                "instrument_token": token,
                "status": "MISMATCH",
                "jaguar_quantity": jaguar_quantity,
                "broker_quantity": broker_quantity,
                "jaguar_side": jaguar.get("side"),
            })

    for token, broker in broker_by_token.items():
        if token not in jaguar_by_token:
            unmatched_broker.append({
                "instrument_token": token,
                "status": "BROKER_POSITION_WITHOUT_JAGUAR",
                "broker_quantity": broker.get("quantity"),
                "broker_symbol": broker.get("broker_symbol"),
            })

    if mismatches or unmatched_broker:
        status = "MISMATCH"
    elif matches:
        status = "MATCH"
    else:
        status = "NO_POSITIONS"

    return {
        "status": status,
        "matches": matches,
        "mismatches": mismatches,
        "unmatched_broker_positions": unmatched_broker,
        "freshness": "CURRENT",
    }


def build_canonical_portfolio_snapshot(
    *,
    portfolio_reader=build_portfolio_snapshot,
    broker_reader=build_broker_position_snapshot,
    account_reader=build_account_snapshot,
) -> dict[str, Any]:
    """Compose Jaguar and broker portfolio authorities without writes."""

    try:
        jaguar = portfolio_reader()

        try:
            broker = broker_reader()
        except BrokerPositionReadModelError:
            broker = {
                "authority": "UPSTOX_SHORT_TERM_POSITIONS",
                "status": "UNAVAILABLE",
                "positions": [],
                "freshness": "UNKNOWN",
                "quantity_source": "UPSTOX_POSITION_API",
            }

        try:
            account = account_reader()
        except AccountReadModelError:
            account = {
                "authority": "UPSTOX_FUND_AND_MARGIN_V3",
                "status": "UNAVAILABLE",
                "available_to_trade": None,
                "cash_available_to_trade": None,
                "pledge_available_to_trade": None,
                "cash_margin_used": None,
                "pledge_margin_used": None,
                "unsettled_profit_today": None,
                "unsettled_profit_previous_days": None,
                "freshness": "UNKNOWN",
            }

        if broker["status"] != "AVAILABLE":
            reconciliation = {
                "status": "BROKER_UNAVAILABLE",
                "matches": [],
                "mismatches": [],
                "unmatched_broker_positions": [],
                "freshness": "UNKNOWN",
            }
        else:
            try:
                reconciliation = _reconcile(
                    jaguar.get("positions", []),
                    broker.get("positions", []),
                )
            except CanonicalPortfolioReadModelError as exc:
                reconciliation = {
                    "status": "UNRECONCILABLE",
                    "matches": [],
                    "mismatches": [{
                        "reason": str(exc),
                    }],
                    "unmatched_broker_positions": [],
                    "freshness": "UNKNOWN",
                }

        result = dict(jaguar)
        result["broker"] = broker
        result["account"] = account
        result["reconciliation"] = reconciliation

        if broker["status"] != "AVAILABLE":
            result["status"] = "BROKER_UNAVAILABLE"
        elif account["status"] != "AVAILABLE":
            result["status"] = "ACCOUNT_UNAVAILABLE"
        elif reconciliation["status"] == "MATCH":
            result["status"] = "AVAILABLE"
        elif reconciliation["status"] == "NO_POSITIONS":
            result["status"] = "AVAILABLE"
        else:
            result["status"] = "RECONCILIATION_MISMATCH"

        return result

    except PortfolioReadModelError as exc:
        raise CanonicalPortfolioReadModelError(
            "Jaguar portfolio read failed"
        ) from exc
    except CanonicalPortfolioReadModelError:
        raise
    except Exception as exc:
        raise CanonicalPortfolioReadModelError(
            "Canonical portfolio read model unavailable"
        ) from exc
