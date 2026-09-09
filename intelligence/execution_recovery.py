"""
Jaguar Quant X
Execution Recovery / Reconciliation

Read-only recovery authority.

This module:
- inspects durable execution intents
- optionally inspects broker observations
- inspects durable trades
- advances only through the V8 execution-intent state machine
- never submits, retries, authorizes, or enables execution
- fails closed on ambiguity or identity conflict
"""

from __future__ import annotations

import sqlite3
from typing import Any, Optional

import research.database as db


_TERMINAL = {
    "RECONCILED",
    "REJECTED",
    "CANCELLED",
    "HALTED",
}

_V9_ORDER_TERMINAL = {
    "FILLED",
    "REJECTED",
    "CANCELLED",
    "HALTED",
}


def _normalize(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _get_trade_by_uuid(trade_uuid: str) -> Optional[dict]:
    conn = db.get_connection()
    try:
        row = conn.execute(
            """
            SELECT *
            FROM trades
            WHERE uuid = ?
            """,
            (trade_uuid,),
        ).fetchone()

        return dict(row) if row is not None else None
    finally:
        conn.close()


def _get_trade_by_authorization_id(
    authorization_id: str,
) -> Optional[dict]:
    conn = db.get_connection()
    try:
        row = conn.execute(
            """
            SELECT *
            FROM trades
            WHERE authorization_id = ?
            ORDER BY rowid DESC
            LIMIT 1
            """,
            (authorization_id,),
        ).fetchone()

        return dict(row) if row is not None else None
    finally:
        conn.close()


def _halt(intent: dict, reason: str) -> dict:
    authorization_id = intent["authorization_id"]

    db.update_execution_intent(
        authorization_id,
        status="HALTED",
    )

    return {
        "authorization_id": authorization_id,
        "previous_status": intent["status"],
        "status": "HALTED",
        "reason": reason,
    }


def _identity_conflict(
    intent: dict,
    broker_order: Optional[dict],
) -> Optional[str]:
    if broker_order is None:
        return None

    if _normalize(
        broker_order.get("authorization_id")
    ) != _normalize(
        intent.get("authorization_id")
    ):
        return "Broker authorization_id mismatch"

    if _normalize(
        broker_order.get("client_order_id")
    ) != _normalize(
        intent.get("client_order_id")
    ):
        return "Broker client_order_id mismatch"

    if intent.get("broker_order_id") is not None:
        if _normalize(
            broker_order.get("broker_order_id")
        ) != _normalize(
            intent.get("broker_order_id")
        ):
            return "Broker broker_order_id mismatch"

    if _normalize(
        broker_order.get("symbol")
    ) != _normalize(
        intent.get("symbol")
    ):
        return "Broker symbol mismatch"

    expected_quantity = float(intent["quantity"])
    broker_quantity = float(
        broker_order.get("requested_qty", 0.0)
    )

    if broker_quantity != expected_quantity:
        return "Broker requested quantity mismatch"

    expected_side = (
        "BUY"
        if _normalize(intent["decision"]).upper() == "LONG"
        else "SELL"
    )

    if _normalize(
        broker_order.get("side")
    ).upper() != expected_side:
        return "Broker side mismatch"

    return None


def _trade_identity_conflict(
    intent: dict,
    trade: Optional[dict],
) -> Optional[str]:
    if trade is None:
        return None

    if _normalize(
        trade.get("uuid")
    ) != _normalize(
        intent.get("trade_uuid")
    ):
        return "Trade UUID mismatch"

    trade_authorization = trade.get("authorization_id")

    # Historical V7 trades may have NULL authorization IDs.
    # Such rows are not eligible for automatic V8 reconciliation.
    if not _normalize(trade_authorization):
        return "Trade missing authorization_id"

    if _normalize(
        trade_authorization
    ) != _normalize(
        intent.get("authorization_id")
    ):
        return "Trade authorization_id mismatch"

    if _normalize(
        trade.get("symbol")
    ) != _normalize(
        intent.get("symbol")
    ):
        return "Trade symbol mismatch"

    if _normalize(
        trade.get("timeframe")
    ) != _normalize(
        intent.get("timeframe")
    ):
        return "Trade timeframe mismatch"

    if _normalize(
        trade.get("mode")
    ).upper() != _normalize(
        intent.get("mode")
    ).upper():
        return "Trade mode mismatch"

    return None



_V9_ORDER_STATUS_MAP = {
    "COMPLETE": "FILLED",
    "COMPLETED": "FILLED",
    "FILLED": "FILLED",
    "PARTIAL": "PARTIAL",
    "PARTIALLY_FILLED": "PARTIAL",
    "REJECTED": "REJECTED",
    "REJECT": "REJECTED",
    "CANCELLED": "CANCELLED",
    "CANCELED": "CANCELLED",
    "SUBMITTED": "SUBMITTED",
    "OPEN": "SUBMITTED",
    "PENDING": "SUBMITTED",
}


def _normalize_v9_order_status(value: Any) -> str:
    status = _normalize(value).upper()

    if status in _V9_ORDER_STATUS_MAP:
        return _V9_ORDER_STATUS_MAP[status]

    raise RuntimeError(
        "FAIL-CLOSED: unknown broker order status"
    )


def _v9_expected_side(intent: dict) -> str:
    decision = _normalize(
        intent.get("decision")
    ).upper()

    if decision == "LONG":
        return "BUY"

    if decision == "SHORT":
        return "SELL"

    raise RuntimeError(
        "FAIL-CLOSED: invalid execution intent decision"
    )


def _v9_validate_order_observation(
    intent: dict,
    durable_order: dict,
    broker_order: dict,
) -> str | None:
    if not isinstance(broker_order, dict):
        return "Broker order observation is not an object"

    authorization_id = _normalize(
        broker_order.get("authorization_id")
    )

    if authorization_id != _normalize(
        intent.get("authorization_id")
    ):
        return "Broker authorization_id mismatch"

    client_order_id = _normalize(
        broker_order.get("client_order_id")
    )

    if client_order_id != _normalize(
        intent.get("client_order_id")
    ):
        return "Broker client_order_id mismatch"

    broker_order_id = _normalize(
        broker_order.get("broker_order_id")
    )

    if not broker_order_id:
        return "Broker order observation missing broker_order_id"

    if broker_order_id != _normalize(
        durable_order.get("broker_order_id")
    ):
        return "Broker order lineage identity mismatch"

    symbol = _normalize(
        broker_order.get("symbol")
    )

    if symbol != _normalize(
        intent.get("symbol")
    ):
        return "Broker symbol mismatch"

    observed_token = _normalize(
        broker_order.get("instrument_token")
    )

    durable_token = _normalize(
        durable_order.get("instrument_token")
    )

    if not observed_token or observed_token != durable_token:
        return "Broker instrument identity mismatch"

    observed_side = _normalize(
        broker_order.get("side")
        or broker_order.get("transaction_type")
    ).upper()

    if observed_side != _v9_expected_side(intent):
        return "Broker side mismatch"

    durable_side = _normalize(
        durable_order.get("transaction_type")
    ).upper()

    if durable_side != _v9_expected_side(intent):
        return "Durable execution-order side mismatch"

    try:
        requested_qty = float(
            broker_order.get("requested_qty")
        )
        durable_requested_qty = float(
            durable_order.get("requested_qty")
        )
    except (TypeError, ValueError):
        return "Broker requested quantity is invalid"

    if requested_qty != durable_requested_qty:
        return "Broker requested quantity mismatch"

    try:
        filled_qty = float(
            broker_order.get("filled_qty", 0.0)
        )
        remaining_qty = float(
            broker_order.get("remaining_qty", 0.0)
        )
    except (TypeError, ValueError):
        return "Broker fill quantity is invalid"

    if filled_qty < 0 or remaining_qty < 0:
        return "Broker quantity cannot be negative"

    if filled_qty > requested_qty:
        return "Broker filled quantity exceeds requested quantity"

    if remaining_qty > requested_qty:
        return "Broker remaining quantity exceeds requested quantity"

    if abs(
        (filled_qty + remaining_qty)
        - requested_qty
    ) > 1e-12:
        return "Broker quantity conservation failed"

    status = _normalize_v9_order_status(
        broker_order.get("status")
    )

    if status == "FILLED":
        if filled_qty != requested_qty or remaining_qty != 0.0:
            return "FILLED broker order quantity state is inconsistent"

    elif status == "PARTIAL":
        if not (
            0.0 < filled_qty < requested_qty
            and remaining_qty > 0.0
        ):
            return "PARTIAL broker order quantity state is inconsistent"

    elif status == "SUBMITTED":
        if filled_qty != 0.0 or remaining_qty != requested_qty:
            return "SUBMITTED broker order quantity state is inconsistent"

    elif status in {"REJECTED", "CANCELLED"}:
        if filled_qty != 0.0:
            return (
                "Rejected/cancelled broker order cannot report a fill "
                "through this contract"
            )

    return None


def _transition_v9_parent(
    authorization_id: str,
    current_status: str,
    target_status: str,
):
    current_status = _normalize(
        current_status
    ).upper()

    target_status = _normalize(
        target_status
    ).upper()

    if current_status == target_status:
        return

    if current_status in _TERMINAL:
        raise RuntimeError(
            "FAIL-CLOSED: terminal execution intent cannot "
            "change during V9 order reconciliation"
        )

    if target_status == "SUBMITTED":
        if current_status != "AUTHORIZED":
            raise RuntimeError(
                "FAIL-CLOSED: invalid V9 parent transition"
            )

        db.update_execution_intent(
            authorization_id,
            status="SUBMITTED",
        )
        return

    if target_status == "PARTIAL":
        if current_status == "AUTHORIZED":
            db.update_execution_intent(
                authorization_id,
                status="SUBMITTED",
            )
            current_status = "SUBMITTED"

        if current_status != "SUBMITTED":
            raise RuntimeError(
                "FAIL-CLOSED: invalid V9 parent transition"
            )

        db.update_execution_intent(
            authorization_id,
            status="PARTIAL",
        )
        return

    if target_status == "FILLED":
        if current_status == "AUTHORIZED":
            db.update_execution_intent(
                authorization_id,
                status="SUBMITTED",
            )
            current_status = "SUBMITTED"

        if current_status not in {
            "SUBMITTED",
            "PARTIAL",
        }:
            raise RuntimeError(
                "FAIL-CLOSED: invalid V9 parent transition"
            )

        db.update_execution_intent(
            authorization_id,
            status="FILLED",
        )
        return

    if target_status in {
        "REJECTED",
        "CANCELLED",
        "HALTED",
    }:
        db.update_execution_intent(
            authorization_id,
            status=target_status,
        )
        return

    raise RuntimeError(
        "FAIL-CLOSED: unsupported V9 parent transition"
    )


def reconcile_execution_order_group(
    authorization_id: str,
    *,
    broker_orders: list[dict],
) -> dict:
    """
    Reconcile one V9 execution intent against its complete
    one-to-many broker-order lineage.

    This function is observation-driven and never submits or
    cancels broker orders.
    """
    if (
        not isinstance(authorization_id, str)
        or not authorization_id.strip()
    ):
        raise ValueError("Invalid authorization_id")

    if not isinstance(broker_orders, list) or not broker_orders:
        raise RuntimeError(
            "FAIL-CLOSED: V9 reconciliation requires broker orders"
        )

    intent_row = db.get_execution_intent(
        authorization_id.strip()
    )

    if intent_row is None:
        raise RuntimeError(
            "FAIL-CLOSED: execution intent not found: "
            f"{authorization_id}"
        )

    intent = dict(intent_row)

    if _normalize(intent.get("mode")).upper() != "LIVE":
        raise RuntimeError(
            "FAIL-CLOSED: V9 order-group reconciliation requires mode=LIVE"
        )

    current_status = _normalize(
        intent.get("status")
    ).upper()

    if current_status in _TERMINAL:
        return {
            "authorization_id": authorization_id,
            "previous_status": current_status,
            "status": current_status,
            "action": "UNCHANGED_TERMINAL",
        }

    durable_orders = [
        dict(row)
        for row in db.list_execution_orders(
            authorization_id
        )
    ]

    if not durable_orders:
        return _halt(
            intent,
            "No durable V9 broker-order lineage exists",
        )

    durable_by_broker_id = {}

    for durable_order in durable_orders:
        broker_id = _normalize(
            durable_order.get("broker_order_id")
        )

        if not broker_id:
            return _halt(
                intent,
                "Durable V9 order is missing broker_order_id",
            )

        if broker_id in durable_by_broker_id:
            return _halt(
                intent,
                "Duplicate durable broker_order_id",
            )

        durable_by_broker_id[broker_id] = durable_order

    observed_by_broker_id = {}

    for broker_order in broker_orders:
        if not isinstance(broker_order, dict):
            return _halt(
                intent,
                "Malformed V9 broker-order observation",
            )

        broker_id = _normalize(
            broker_order.get("broker_order_id")
        )

        if not broker_id:
            return _halt(
                intent,
                "Broker order observation missing broker_order_id",
            )

        if broker_id in observed_by_broker_id:
            return _halt(
                intent,
                "Duplicate broker_order_id in observation set",
            )

        observed_by_broker_id[broker_id] = broker_order

    durable_ids = set(durable_by_broker_id)
    observed_ids = set(observed_by_broker_id)

    if durable_ids != observed_ids:
        return _halt(
            intent,
            "Broker observation set does not match durable order lineage",
        )

    expected_quantity = float(intent["quantity"])

    aggregate_requested = 0.0
    aggregate_filled = 0.0
    aggregate_remaining = 0.0

    normalized_statuses = []

    for broker_id in sorted(observed_ids):
        durable_order = durable_by_broker_id[
            broker_id
        ]

        broker_order = observed_by_broker_id[
            broker_id
        ]

        conflict = _v9_validate_order_observation(
            intent,
            durable_order,
            broker_order,
        )

        if conflict:
            return _halt(
                intent,
                conflict,
            )

        requested_qty = float(
            broker_order["requested_qty"]
        )
        filled_qty = float(
            broker_order.get("filled_qty", 0.0)
        )
        remaining_qty = float(
            broker_order.get("remaining_qty", 0.0)
        )
        normalized_status = _normalize_v9_order_status(
            broker_order.get("status")
        )

        aggregate_requested += requested_qty
        aggregate_filled += filled_qty
        aggregate_remaining += remaining_qty
        normalized_statuses.append(
            normalized_status
        )

        durable_status = _normalize(
            durable_order.get("status")
        ).upper()

        if durable_status in _V9_ORDER_TERMINAL:
            if durable_status != normalized_status:
                return _halt(
                    intent,
                    "Terminal broker-order status changed",
                )

            if (
                float(durable_order["filled_qty"])
                != filled_qty
                or float(durable_order["remaining_qty"])
                != remaining_qty
            ):
                return _halt(
                    intent,
                    "Terminal broker-order quantity changed",
                )

            continue

        try:
            db.update_execution_order(
                durable_order["order_lineage_id"],
                status=normalized_status,
                filled_qty=filled_qty,
                remaining_qty=remaining_qty,
                average_fill_price=(
                    broker_order.get("average_fill_price")
                ),
                raw_status=broker_order.get("raw_status"),
            )
        except Exception as exc:
            return _halt(
                intent,
                "V9 broker-order persistence failed: "
                f"{type(exc).__name__}",
            )

    if abs(
        aggregate_requested - expected_quantity
    ) > 1e-12:
        return _halt(
            intent,
            "Aggregate child requested quantity does not match intent",
        )

    if aggregate_filled > expected_quantity:
        return _halt(
            intent,
            "Aggregate filled quantity exceeds intent quantity",
        )

    if aggregate_remaining > expected_quantity:
        return _halt(
            intent,
            "Aggregate remaining quantity exceeds intent quantity",
        )

    if abs(
        (aggregate_filled + aggregate_remaining)
        - expected_quantity
    ) > 1e-12:
        return _halt(
            intent,
            "Aggregate quantity conservation failed",
        )

    all_rejected = all(
        status == "REJECTED"
        for status in normalized_statuses
    )

    all_cancelled = all(
        status == "CANCELLED"
        for status in normalized_statuses
    )

    if aggregate_filled == expected_quantity:
        try:
            _transition_v9_parent(
                authorization_id,
                current_status,
                "FILLED",
            )
        except Exception as exc:
            return _halt(
                intent,
                "V9 parent FILLED persistence failed: "
                f"{type(exc).__name__}",
            )

        return {
            "authorization_id": authorization_id,
            "previous_status": current_status,
            "status": "FILLED",
            "requested_quantity": expected_quantity,
            "filled_quantity": aggregate_filled,
            "remaining_quantity": aggregate_remaining,
            "order_count": len(broker_orders),
        }

    if aggregate_filled == 0.0 and all_rejected:
        try:
            _transition_v9_parent(
                authorization_id,
                current_status,
                "REJECTED",
            )
        except Exception as exc:
            return _halt(
                intent,
                "V9 parent REJECTED persistence failed: "
                f"{type(exc).__name__}",
            )

        return {
            "authorization_id": authorization_id,
            "previous_status": current_status,
            "status": "REJECTED",
            "requested_quantity": expected_quantity,
            "filled_quantity": 0.0,
            "remaining_quantity": aggregate_remaining,
            "order_count": len(broker_orders),
        }

    if aggregate_filled == 0.0 and all_cancelled:
        try:
            _transition_v9_parent(
                authorization_id,
                current_status,
                "CANCELLED",
            )
        except Exception as exc:
            return _halt(
                intent,
                "V9 parent CANCELLED persistence failed: "
                f"{type(exc).__name__}",
            )

        return {
            "authorization_id": authorization_id,
            "previous_status": current_status,
            "status": "CANCELLED",
            "requested_quantity": expected_quantity,
            "filled_quantity": 0.0,
            "remaining_quantity": aggregate_remaining,
            "order_count": len(broker_orders),
        }

    if aggregate_remaining > 0.0:
        try:
            _transition_v9_parent(
                authorization_id,
                current_status,
                "PARTIAL"
                if aggregate_filled > 0.0
                else "SUBMITTED",
            )
        except Exception as exc:
            return _halt(
                intent,
                "V9 parent partial persistence failed: "
                f"{type(exc).__name__}",
            )

        return {
            "authorization_id": authorization_id,
            "previous_status": current_status,
            "status": (
                "PARTIAL"
                if aggregate_filled > 0.0
                else "SUBMITTED"
            ),
            "requested_quantity": expected_quantity,
            "filled_quantity": aggregate_filled,
            "remaining_quantity": aggregate_remaining,
            "order_count": len(broker_orders),
        }

    return _halt(
        intent,
        "Broker execution is incomplete with no remaining quantity",
    )


def reconcile_execution_intent(
    authorization_id: str,
    *,
    broker_order: Optional[dict] = None,
    broker_position: Optional[dict] = None,
) -> dict:
    """
    Reconcile one non-terminal execution intent.

    broker_order / broker_position are observations only.
    This function never queries a broker itself and never submits anything.
    """

    if not isinstance(authorization_id, str) or not authorization_id.strip():
        raise ValueError("Invalid authorization_id")

    intent = db.get_execution_intent(
        authorization_id.strip()
    )

    if intent is None:
        raise RuntimeError(
            "FAIL-CLOSED: execution intent not found: "
            f"{authorization_id}"
        )

    intent = dict(intent)
    current_status = _normalize(intent.get("status")).upper()

    if current_status in _TERMINAL:
        return {
            "authorization_id": authorization_id,
            "previous_status": current_status,
            "status": current_status,
            "action": "UNCHANGED_TERMINAL",
        }

    # Any supplied broker evidence must correlate positively.
    broker_conflict = _identity_conflict(
        intent,
        broker_order,
    )

    if broker_conflict:
        return _halt(
            intent,
            broker_conflict,
        )

    trade = _get_trade_by_uuid(
        intent["trade_uuid"]
    )

    # If the expected UUID is absent, also look by authoritative
    # authorization_id so contradictory duplicate data can be detected.
    auth_trade = _get_trade_by_authorization_id(
        authorization_id
    )

    if trade is None and auth_trade is not None:
        return _halt(
            intent,
            "Trade authorization exists under a different UUID",
        )

    trade_conflict = _trade_identity_conflict(
        intent,
        trade,
    )

    if trade_conflict:
        return _halt(
            intent,
            trade_conflict,
        )

    if broker_position is not None:
        if _normalize(
            broker_position.get("authorization_id")
        ) != _normalize(authorization_id):
            return _halt(
                intent,
                "Broker position authorization_id mismatch",
            )

        position_quantity = float(
            broker_position.get("quantity", 0.0)
        )

        expected_quantity = float(
            intent["quantity"]
        )

        if position_quantity != expected_quantity:
            return _halt(
                intent,
                "Broker position quantity mismatch",
            )

    # ------------------------------------------------------------
    # AUTHORIZED
    # ------------------------------------------------------------
    if current_status == "AUTHORIZED":
        if broker_order is None:
            # There is no external evidence that the order reached
            # the broker. Because recovery must never create an order,
            # the only safe result is HALTED.
            return _halt(
                intent,
                "AUTHORIZED intent has no broker evidence",
            )

        broker_status = _normalize(
            broker_order.get("status")
        ).upper()

        if broker_status in {"REJECTED", "CANCELLED"}:
            db.update_execution_intent(
                authorization_id,
                status="REJECTED"
                if broker_status == "REJECTED"
                else "CANCELLED",
            )

            return {
                "authorization_id": authorization_id,
                "previous_status": current_status,
                "status": (
                    "REJECTED"
                    if broker_status == "REJECTED"
                    else "CANCELLED"
                ),
                "reason": f"Broker reported {broker_status}",
            }

        broker_order_id = broker_order.get(
            "broker_order_id"
        )

        if not isinstance(
            broker_order_id,
            str,
        ) or not broker_order_id.strip():
            return _halt(
                intent,
                "Broker evidence missing broker_order_id",
            )

        db.update_execution_intent(
            authorization_id,
            broker_order_id=broker_order_id,
            status="SUBMITTED",
        )

        return {
            "authorization_id": authorization_id,
            "previous_status": current_status,
            "status": "SUBMITTED",
            "broker_order_id": broker_order_id,
        }

    # ------------------------------------------------------------
    # SUBMITTED
    # ------------------------------------------------------------
    if current_status == "SUBMITTED":
        if broker_order is None:
            return _halt(
                intent,
                "SUBMITTED intent has no matching broker evidence",
            )

        if trade is None:
            # Broker side is known, but durable trade has not been
            # established. Leave non-terminal; another recovery pass
            # can reconcile once the trade exists.
            return {
                "authorization_id": authorization_id,
                "previous_status": current_status,
                "status": "SUBMITTED",
                "action": "WAIT_FOR_TRADE",
            }

        broker_order_id = _normalize(
            broker_order.get("broker_order_id")
        )

        intent_broker_order_id = _normalize(
            intent.get("broker_order_id")
        )

        if not broker_order_id:
            return _halt(
                intent,
                "Broker evidence missing broker_order_id",
            )

        if broker_order_id != intent_broker_order_id:
            return _halt(
                intent,
                "Broker order identity does not match intent",
            )

        broker_status = _normalize(
            broker_order.get("status")
        ).upper()

        if broker_status in {"REJECTED", "CANCELLED"}:
            db.update_execution_intent(
                authorization_id,
                status=(
                    "REJECTED"
                    if broker_status == "REJECTED"
                    else "CANCELLED"
                ),
            )

            return {
                "authorization_id": authorization_id,
                "previous_status": current_status,
                "status": (
                    "REJECTED"
                    if broker_status == "REJECTED"
                    else "CANCELLED"
                ),
                "reason": f"Broker reported {broker_status}",
            }

        if broker_status != "FILLED":
            return {
                "authorization_id": authorization_id,
                "previous_status": current_status,
                "status": "SUBMITTED",
                "action": "WAIT_FOR_FILL",
            }

        filled_quantity = float(
            broker_order.get("filled_qty", 0.0)
        )
        expected_quantity = float(
            intent["quantity"]
        )

        if filled_quantity != expected_quantity:
            return _halt(
                intent,
                "Filled quantity does not match intent quantity",
            )

        trade_status = _normalize(
            trade.get("status")
        ).upper()

        if trade_status != "OPEN":
            return _halt(
                intent,
                f"Unexpected trade lifecycle status: {trade_status}",
            )

        if broker_position is not None:
            position_quantity = float(
                broker_position.get("quantity", 0.0)
            )

            if position_quantity != expected_quantity:
                return _halt(
                    intent,
                    "Filled broker position quantity mismatch",
                )

        db.update_execution_intent(
            authorization_id,
            status="RECONCILED",
        )

        return {
            "authorization_id": authorization_id,
            "previous_status": current_status,
            "status": "RECONCILED",
            "broker_order_id": broker_order_id,
            "trade_uuid": intent["trade_uuid"],
        }

    # Unknown non-terminal state: fail closed.
    return _halt(
        intent,
        f"Unknown execution-intent state: {current_status}",
    )


def reconcile_all(
    broker_observer=None,
) -> list[dict]:
    """
    Reconcile every non-terminal execution intent.

    broker_observer is an optional read-only callback:

        broker_observer(intent) ->
            {
                "order": dict | None,
                "position": dict | None,
            }

    The callback must not submit or mutate broker state.
    """

    results = []

    for intent_row in db.list_non_terminal_execution_intents():
        intent = dict(intent_row)

        observation = {
            "order": None,
            "position": None,
        }

        if broker_observer is not None:
            observation = broker_observer(intent) or {}

        results.append(
            reconcile_execution_intent(
                intent["authorization_id"],
                broker_order=observation.get("order"),
                broker_position=observation.get("position"),
            )
        )

    return results
