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
