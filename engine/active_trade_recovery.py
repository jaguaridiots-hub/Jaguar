"""Fail-closed reconstruction of an already-open PAPER trade."""

import hashlib
import json
import math
from datetime import datetime

from research.database import (
    get_connection,
    get_active_trade_lifecycle,
    update_active_trade_lifecycle,
)


class ActiveTradeRecoveryError(RuntimeError):
    """Raised when an active trade cannot be reconstructed safely."""


def _positive_float(value, field):
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ActiveTradeRecoveryError(
            f"FAIL-CLOSED: Invalid recovered {field}"
        ) from exc

    if not math.isfinite(number) or number <= 0:
        raise ActiveTradeRecoveryError(
            f"FAIL-CLOSED: Invalid recovered {field}"
        )

    return number


def _same(left, right):
    return math.isclose(
        float(left),
        float(right),
        rel_tol=0.0,
        abs_tol=1e-8,
    )



def _load_durable_fill(
    trade,
    *,
    trade_uuid,
    authorization_id,
    expected_symbol,
):
    """Read and verify the immutable actual fill from snapshot_open."""

    raw_snapshot = trade.get("snapshot_open")
    stored_checksum = trade.get("snapshot_open_checksum")

    if (
        not isinstance(raw_snapshot, str)
        or not raw_snapshot.strip()
        or not isinstance(stored_checksum, str)
        or not stored_checksum.strip()
    ):
        raise ActiveTradeRecoveryError(
            "FAIL-CLOSED: Durable trade snapshot/fingerprint missing"
        )

    try:
        snapshot = json.loads(raw_snapshot)
    except (TypeError, ValueError) as exc:
        raise ActiveTradeRecoveryError(
            "FAIL-CLOSED: Durable trade snapshot is invalid"
        ) from exc

    if not isinstance(snapshot, dict):
        raise ActiveTradeRecoveryError(
            "FAIL-CLOSED: Durable trade snapshot is not an object"
        )

    expected_checksum = hashlib.sha256(
        json.dumps(
            snapshot,
            sort_keys=True,
        ).encode()
    ).hexdigest()

    if stored_checksum != expected_checksum:
        raise ActiveTradeRecoveryError(
            "FAIL-CLOSED: Durable trade snapshot checksum mismatch"
        )

    execution = snapshot.get(
        "enterprise_execution"
    )

    if not isinstance(execution, dict):
        raise ActiveTradeRecoveryError(
            "FAIL-CLOSED: Durable execution snapshot is missing"
        )

    snapshot_trade_uuid = execution.get(
        "trade_uuid"
    )

    if snapshot_trade_uuid != trade_uuid:
        raise ActiveTradeRecoveryError(
            "FAIL-CLOSED: Durable snapshot trade UUID mismatch"
        )

    snapshot_authorization_id = execution.get(
        "authorization_id"
    )

    if snapshot_authorization_id != authorization_id:
        raise ActiveTradeRecoveryError(
            "FAIL-CLOSED: Durable snapshot authorization mismatch"
        )

    snapshot_symbol = str(
        execution.get("symbol", "")
    ).upper().strip()

    if snapshot_symbol != expected_symbol:
        raise ActiveTradeRecoveryError(
            "FAIL-CLOSED: Durable snapshot symbol mismatch"
        )

    fill_price = _positive_float(
        execution.get("fill_price"),
        "durable fill price",
    )

    filled_quantity = _positive_float(
        execution.get("filled_quantity"),
        "durable filled quantity",
    )

    return {
        "fill_price": fill_price,
        "filled_quantity": filled_quantity,
        "client_order_id": str(
            execution.get("client_order_id", "")
        ).strip(),
    }

def recover_active_trade_plan(
    trade_uuid,
    position,
    symbol=None,
):
    if not isinstance(trade_uuid, str) or not trade_uuid.strip():
        raise ActiveTradeRecoveryError(
            "FAIL-CLOSED: Missing restored trade UUID"
        )

    direction = str(
        getattr(position, "position", "NONE")
    ).upper().strip()

    if direction not in {"LONG", "SHORT"}:
        raise ActiveTradeRecoveryError(
            "FAIL-CLOSED: Invalid active position during recovery"
        )

    conn = get_connection()

    try:
        trade_row = conn.execute(
            """
            SELECT *
            FROM trades
            WHERE uuid = ?
            LIMIT 1
            """,
            (trade_uuid,),
        ).fetchone()

        if trade_row is None:
            raise ActiveTradeRecoveryError(
                "FAIL-CLOSED: Restored trade row not found"
            )

        trade = dict(trade_row)

        if str(trade.get("status", "")).upper().strip() != "OPEN":
            raise ActiveTradeRecoveryError(
                "FAIL-CLOSED: Restored trade is not OPEN"
            )

        if trade.get("close_time") is not None:
            raise ActiveTradeRecoveryError(
                "FAIL-CLOSED: Restored trade already has close_time"
            )

        trade_symbol = str(
            trade.get("symbol", "")
        ).upper().strip()

        if symbol is not None:
            expected_symbol = str(symbol).upper().strip()

            if trade_symbol != expected_symbol:
                raise ActiveTradeRecoveryError(
                    "FAIL-CLOSED: Restored trade symbol mismatch"
                )

        authorization_id = trade.get("authorization_id")

        if (
            not isinstance(authorization_id, str)
            or not authorization_id.strip()
        ):
            raise ActiveTradeRecoveryError(
                "FAIL-CLOSED: Restored trade has no authorization ID"
            )

        intent_row = conn.execute(
            """
            SELECT *
            FROM execution_intents
            WHERE authorization_id = ?
            LIMIT 1
            """,
            (authorization_id,),
        ).fetchone()

        if intent_row is None:
            raise ActiveTradeRecoveryError(
                "FAIL-CLOSED: Restored execution intent not found"
            )

        intent = dict(intent_row)

        if intent.get("trade_uuid") != trade_uuid:
            raise ActiveTradeRecoveryError(
                "FAIL-CLOSED: Trade UUID lineage mismatch"
            )

        if str(intent.get("mode", "")).upper().strip() != "PAPER":
            raise ActiveTradeRecoveryError(
                "FAIL-CLOSED: Non-PAPER execution cannot restore "
                "PositionManager"
            )

        if str(intent.get("status", "")).upper().strip() != "RECONCILED":
            raise ActiveTradeRecoveryError(
                "FAIL-CLOSED: Execution intent is not RECONCILED"
            )

        if not str(intent.get("client_order_id", "")).strip():
            raise ActiveTradeRecoveryError(
                "FAIL-CLOSED: Recovered execution has no client order ID"
            )

        if not str(intent.get("broker_order_id", "")).strip():
            raise ActiveTradeRecoveryError(
                "FAIL-CLOSED: Recovered execution has no broker order ID"
            )

        decision = str(
            intent.get("decision", "")
        ).upper().strip()

        if decision not in {"LONG", "SHORT"}:
            raise ActiveTradeRecoveryError(
                "FAIL-CLOSED: Invalid recovered execution direction"
            )

        if decision != direction:
            raise ActiveTradeRecoveryError(
                "FAIL-CLOSED: Execution direction conflicts "
                "with PositionManager"
            )

        durable_fill = _load_durable_fill(
            trade,
            trade_uuid=trade_uuid,
            authorization_id=authorization_id,
            expected_symbol=trade_symbol,
        )

        entry = _positive_float(
            getattr(position, "entry", 0.0),
            "entry",
        )

        durable_fill_price = durable_fill["fill_price"]

        if not _same(entry, durable_fill_price):
            raise ActiveTradeRecoveryError(
                "FAIL-CLOSED: Position entry conflicts with durable fill"
            )

        if (
            durable_fill["client_order_id"]
            and durable_fill["client_order_id"]
            != str(intent.get("client_order_id", "")).strip()
        ):
            raise ActiveTradeRecoveryError(
                "FAIL-CLOSED: Durable fill client order ID mismatch"
            )

        original_stop = _positive_float(
            intent.get("stop_loss"),
            "stop loss",
        )

        trade_stop = _positive_float(
            trade.get("stop_loss"),
            "trade stop",
        )

        if not _same(original_stop, trade_stop):
            raise ActiveTradeRecoveryError(
                "FAIL-CLOSED: Execution stop conflicts with durable trade"
            )

        quantity = _positive_float(
            intent.get("quantity"),
            "execution quantity",
        )

        filled_quantity = durable_fill["filled_quantity"]

        if not _same(
            filled_quantity,
            quantity,
        ):
            raise ActiveTradeRecoveryError(
                "FAIL-CLOSED: Durable fill quantity conflicts "
                "with execution quantity"
            )

        position_size = _positive_float(
            getattr(position, "position_size", 0.0),
            "position size",
        )

        if not _same(quantity, position_size):
            raise ActiveTradeRecoveryError(
                "FAIL-CLOSED: Position size conflicts with execution quantity"
            )

        rows = [
            dict(row)
            for row in conn.execute(
                """
                SELECT *
                FROM execution_protection
                WHERE authorization_id = ?
                ORDER BY protection_type, target_index
                """,
                (authorization_id,),
            ).fetchall()
        ]

        # PAPER recovery requires exactly one stop and three take-profits.
        # No extra durable protection rows are permitted.
        if len(rows) != 4:
            raise ActiveTradeRecoveryError(
                "FAIL-CLOSED: Durable PAPER protection set has "
                "unexpected cardinality"
            )

        # Every VERIFIED protection must represent the complete durable fill.
        for protection_row in rows:
            if str(
                protection_row.get("status", "")
            ).upper().strip() != "VERIFIED":
                raise ActiveTradeRecoveryError(
                    "FAIL-CLOSED: Durable PAPER protection is not VERIFIED"
                )

            requested_qty = _positive_float(
                protection_row.get("requested_qty"),
                "durable protection requested quantity",
            )

            verified_qty = _positive_float(
                protection_row.get("verified_qty"),
                "durable protection verified quantity",
            )

            if not _same(
                requested_qty,
                filled_quantity,
            ):
                raise ActiveTradeRecoveryError(
                    "FAIL-CLOSED: Durable protection requested "
                    "quantity conflicts with fill"
                )

            if not _same(
                verified_qty,
                filled_quantity,
            ):
                raise ActiveTradeRecoveryError(
                    "FAIL-CLOSED: Durable protection verified "
                    "quantity conflicts with fill"
                )

        stop_rows = [
            row
            for row in rows
            if str(row.get("protection_type", "")).upper().strip()
            == "STOP_LOSS"
        ]

        if len(stop_rows) != 1:
            raise ActiveTradeRecoveryError(
                "FAIL-CLOSED: Invalid durable stop-protection set"
            )

        stop_row = stop_rows[0]

        if str(stop_row.get("status", "")).upper().strip() != "VERIFIED":
            raise ActiveTradeRecoveryError(
                "FAIL-CLOSED: Durable stop protection is not VERIFIED"
            )

        stop_price = _positive_float(
            stop_row.get("requested_price"),
            "durable stop protection",
        )

        verified_stop_price = _positive_float(
            stop_row.get("verified_price"),
            "verified durable stop protection",
        )

        if not _same(stop_price, original_stop):
            raise ActiveTradeRecoveryError(
                "FAIL-CLOSED: Durable stop conflicts with execution"
            )

        if not _same(stop_price, verified_stop_price):
            raise ActiveTradeRecoveryError(
                "FAIL-CLOSED: Durable stop verification mismatch"
            )

        targets = {}

        for row in rows:
            if (
                str(row.get("protection_type", "")).upper().strip()
                != "TAKE_PROFIT"
            ):
                continue

            if str(row.get("status", "")).upper().strip() != "VERIFIED":
                raise ActiveTradeRecoveryError(
                    "FAIL-CLOSED: Durable take-profit protection "
                    "is not VERIFIED"
                )

            target_index = row.get("target_index")

            if isinstance(target_index, bool):
                raise ActiveTradeRecoveryError(
                    "FAIL-CLOSED: Invalid take-profit target index"
                )

            try:
                target_index = int(target_index)
            except (TypeError, ValueError) as exc:
                raise ActiveTradeRecoveryError(
                    "FAIL-CLOSED: Invalid take-profit target index"
                ) from exc

            if target_index in targets:
                raise ActiveTradeRecoveryError(
                    "FAIL-CLOSED: Duplicate take-profit target index"
                )

            requested_price = _positive_float(
                row.get("requested_price"),
                f"TP{target_index + 1}",
            )

            verified_price = _positive_float(
                row.get("verified_price"),
                f"verified TP{target_index + 1}",
            )

            if not _same(requested_price, verified_price):
                raise ActiveTradeRecoveryError(
                    "FAIL-CLOSED: Take-profit verification mismatch"
                )

            targets[target_index] = requested_price

        if set(targets) != {0, 1, 2}:
            raise ActiveTradeRecoveryError(
                "FAIL-CLOSED: Durable TP1/TP2/TP3 contract is not exact"
            )

        tp1 = targets[0]
        tp2 = targets[1]
        tp3 = targets[2]

        intent_tp1 = _positive_float(
            intent.get("take_profit"),
            "execution TP1",
        )

        trade_tp1 = _positive_float(
            trade.get("take_profit"),
            "trade TP1",
        )

        position_tp1 = _positive_float(
            getattr(position, "take_profit", 0.0),
            "position TP1",
        )

        if not _same(intent_tp1, tp1):
            raise ActiveTradeRecoveryError(
                "FAIL-CLOSED: Execution TP1 conflicts with protection"
            )

        if not _same(trade_tp1, tp1):
            raise ActiveTradeRecoveryError(
                "FAIL-CLOSED: Trade TP1 conflicts with protection"
            )

        if not _same(position_tp1, tp1):
            raise ActiveTradeRecoveryError(
                "FAIL-CLOSED: Position TP1 conflicts with protection"
            )

        if direction == "LONG":
            valid_geometry = (
                original_stop < entry
                and entry < tp1 < tp2 < tp3
            )
        else:
            valid_geometry = (
                original_stop > entry
                and entry > tp1 > tp2 > tp3
            )

        if not valid_geometry:
            raise ActiveTradeRecoveryError(
                "FAIL-CLOSED: Recovered trade geometry is invalid"
            )

        return {
            "Direction": (
                "BUY"
                if decision == "LONG"
                else "SELL"
            ),
            "Entry": durable_fill_price,
            "StopLoss": original_stop,
            "TP1": tp1,
            "TP2": tp2,
            "TP3": tp3,
            "PositionSize": position_size,
            "AuthorizationID": authorization_id,
            "TradeUUID": trade_uuid,
        }

    finally:
        conn.close()



def recover_active_trade_from_durable_lifecycle(
    *,
    position,
    manager,
    symbol,
):
    """Reconstruct an already-open PAPER trade after local-cache loss.

    Returns the canonical recovery plan when exactly one valid durable
    lifecycle exists for the requested symbol. Returns None when there is
    no durable lifecycle candidate; the caller must retain the existing
    orphan barrier in that case.
    """

    expected_symbol = str(
        symbol or ""
    ).upper().strip()

    if not expected_symbol:
        raise ActiveTradeRecoveryError(
            "FAIL-CLOSED: Invalid recovery symbol"
        )

    conn = get_connection()

    try:
        rows = conn.execute(
            """
            SELECT
                l.trade_uuid,
                l.authorization_id,
                l.symbol AS lifecycle_symbol,
                t.uuid AS trade_uuid_row,
                t.status AS trade_status,
                t.close_time
            FROM active_trade_lifecycle AS l
            JOIN trades AS t
              ON t.uuid = l.trade_uuid
            JOIN execution_intents AS i
              ON i.authorization_id = l.authorization_id
             AND i.trade_uuid = l.trade_uuid
            WHERE l.symbol = ?
              AND t.symbol = ?
              AND t.status = 'OPEN'
              AND t.close_time IS NULL
            ORDER BY t.open_time ASC
            """,
            (
                expected_symbol,
                expected_symbol,
            ),
        ).fetchall()

        if not rows:
            return None

        if len(rows) != 1:
            raise ActiveTradeRecoveryError(
                "FAIL-CLOSED: Multiple durable active trade "
                "lifecycles found for symbol"
            )

        candidate = dict(rows[0])

        trade_uuid = candidate.get("trade_uuid")

        if (
            not isinstance(trade_uuid, str)
            or not trade_uuid.strip()
        ):
            raise ActiveTradeRecoveryError(
                "FAIL-CLOSED: Durable lifecycle has invalid trade UUID"
            )

    finally:
        conn.close()

    lifecycle = get_active_trade_lifecycle(
        trade_uuid.strip()
    )

    if lifecycle is None:
        raise ActiveTradeRecoveryError(
            "FAIL-CLOSED: Durable lifecycle disappeared during recovery"
        )

    if (
        str(lifecycle["symbol"]).upper().strip()
        != expected_symbol
    ):
        raise ActiveTradeRecoveryError(
            "FAIL-CLOSED: Durable lifecycle symbol mismatch"
        )

    direction = str(
        lifecycle["position"]
    ).upper().strip()

    if direction not in {"LONG", "SHORT"}:
        raise ActiveTradeRecoveryError(
            "FAIL-CLOSED: Invalid durable recovery position"
        )

    # The lifecycle is only eligible to restore a nonterminal position.
    if bool(lifecycle["trade_closed"]):
        raise ActiveTradeRecoveryError(
            "FAIL-CLOSED: Durable lifecycle is terminal"
        )

    # Reconstruct the PositionManager from the immutable execution/trade
    # contract first. recover_active_trade_plan() performs the complete
    # execution/protection lineage validation.
    recovery_seed = conn = get_connection()

    try:
        trade_row = conn.execute(
            """
            SELECT *
            FROM trades
            WHERE uuid = ?
              AND status = 'OPEN'
              AND close_time IS NULL
            LIMIT 1
            """,
            (trade_uuid,),
        ).fetchone()

        if trade_row is None:
            raise ActiveTradeRecoveryError(
                "FAIL-CLOSED: Durable OPEN trade disappeared during recovery"
            )

        intent_row = conn.execute(
            """
            SELECT *
            FROM execution_intents
            WHERE authorization_id = ?
              AND trade_uuid = ?
            LIMIT 1
            """,
            (
                lifecycle["authorization_id"],
                trade_uuid,
            ),
        ).fetchone()

        if intent_row is None:
            raise ActiveTradeRecoveryError(
                "FAIL-CLOSED: Durable execution lineage disappeared "
                "during recovery"
            )

        trade = dict(trade_row)
        intent = dict(intent_row)

        # FAIL-CLOSED: the durable trade row must belong to the same
        # canonical authorization identity as the active lifecycle and
        # reconciled execution intent before PositionManager mutation.
        trade_authorization_id = str(
            trade.get("authorization_id", "")
        ).strip()
        lifecycle_authorization_id = str(
            lifecycle["authorization_id"]
        ).strip()

        if (
            not trade_authorization_id
            or trade_authorization_id
            != lifecycle_authorization_id
        ):
            raise ActiveTradeRecoveryError(
                "FAIL-CLOSED: Durable trade authorization "
                "conflicts with active lifecycle"
            )

    finally:
        recovery_seed.close()

    if str(intent.get("mode", "")).upper().strip() != "PAPER":
        raise ActiveTradeRecoveryError(
            "FAIL-CLOSED: Only PAPER trades may be restored"
        )

    decision = str(
        intent.get("decision", "")
    ).upper().strip()

    expected_decision = (
        "LONG"
        if direction == "LONG"
        else "SHORT"
    )

    if decision != expected_decision:
        raise ActiveTradeRecoveryError(
            "FAIL-CLOSED: Durable recovery direction mismatch"
        )

    durable_fill = _load_durable_fill(
        trade,
        trade_uuid=trade_uuid,
        authorization_id=lifecycle["authorization_id"],
        expected_symbol=expected_symbol,
    )

    entry = durable_fill["fill_price"]

    original_stop = _positive_float(
        intent.get("stop_loss"),
        "durable execution stop",
    )

    quantity = _positive_float(
        intent.get("quantity"),
        "durable execution quantity",
    )

    if not _same(
        durable_fill["filled_quantity"],
        quantity,
    ):
        raise ActiveTradeRecoveryError(
            "FAIL-CLOSED: Durable fill quantity conflicts "
            "with execution quantity"
        )

    # This exactly reproduces the PAPER post-fill calculation:
    # abs(fill_price - authorized_stop) * position_size.
    initial_risk = abs(
        entry - original_stop
    ) * quantity

    if (
        not math.isfinite(initial_risk)
        or initial_risk <= 0
    ):
        raise ActiveTradeRecoveryError(
            "FAIL-CLOSED: Invalid reconstructed initial risk"
        )

    first_target = _positive_float(
        intent.get("take_profit"),
        "durable execution TP1",
    )

    try:
        position.open_trade(
            direction,
            entry,
            original_stop,
            first_target,
            position_size=quantity,
            initial_risk=initial_risk,
        )
        position.set_trade_uuid(
            trade_uuid
        )
    except Exception as exc:
        raise ActiveTradeRecoveryError(
            "FAIL-CLOSED: Unable to reconstruct PositionManager"
        ) from exc

    plan = recover_active_trade_plan(
        trade_uuid,
        position,
        expected_symbol,
    )

    current_stop = _positive_float(
        lifecycle["current_stop"],
        "durable lifecycle current stop",
    )

    # Validate the current-stop state against the deterministic lifecycle
    # transitions implemented by TradeManager.
    tp1_hit = bool(lifecycle["tp1_hit"])
    tp2_hit = bool(lifecycle["tp2_hit"])
    break_even = bool(lifecycle["break_even"])
    trailing = bool(lifecycle["trailing"])

    # These relationships are monotonic in the production manager:
    # TP1 -> break-even, TP2 -> trailing.
    if break_even != tp1_hit:
        raise ActiveTradeRecoveryError(
            "FAIL-CLOSED: Durable break-even/TP1 lifecycle mismatch"
        )

    if trailing != tp2_hit:
        raise ActiveTradeRecoveryError(
            "FAIL-CLOSED: Durable trailing/TP2 lifecycle mismatch"
        )

    if tp2_hit and not tp1_hit:
        raise ActiveTradeRecoveryError(
            "FAIL-CLOSED: Durable TP2 lifecycle precedes TP1"
        )

    if not tp1_hit:
        if not _same(
            current_stop,
            plan["StopLoss"],
        ):
            raise ActiveTradeRecoveryError(
                "FAIL-CLOSED: Pre-TP1 durable stop is inconsistent"
            )

    elif not tp2_hit:
        if not _same(
            current_stop,
            plan["Entry"],
        ):
            raise ActiveTradeRecoveryError(
                "FAIL-CLOSED: Break-even durable stop is inconsistent"
            )

    else:
        if direction == "LONG":
            if current_stop < float(plan["Entry"]):
                raise ActiveTradeRecoveryError(
                    "FAIL-CLOSED: LONG trailing stop regressed below entry"
                )
        else:
            if current_stop > float(plan["Entry"]):
                raise ActiveTradeRecoveryError(
                    "FAIL-CLOSED: SHORT trailing stop regressed above entry"
                )

    position.update_stop_loss(
        current_stop
    )

    manager_snapshot = {
        "position_open": True,
        "trade_closed": False,
        "break_even": bool(lifecycle["break_even"]),
        "trailing": bool(lifecycle["trailing"]),
        "tp1_hit": bool(lifecycle["tp1_hit"]),
        "tp2_hit": bool(lifecycle["tp2_hit"]),
    }

    try:
        manager.restore(
            manager_snapshot
        )
    except Exception as exc:
        raise ActiveTradeRecoveryError(
            "FAIL-CLOSED: Durable TradeManager lifecycle "
            "cannot be restored"
        ) from exc

    return plan

def persist_active_trade_lifecycle(
    *,
    trade_uuid,
    position,
    manager,
    plan,
    symbol,
):
    """Persist non-terminal active-management state using V11 CAS."""

    if (
        not isinstance(trade_uuid, str)
        or not trade_uuid.strip()
    ):
        raise ActiveTradeRecoveryError(
            "FAIL-CLOSED: Missing active lifecycle trade UUID"
        )

    lifecycle = get_active_trade_lifecycle(
        trade_uuid.strip()
    )

    if lifecycle is None:
        raise ActiveTradeRecoveryError(
            "FAIL-CLOSED: Active lifecycle record not found"
        )

    expected_symbol = str(
        symbol or ""
    ).upper().strip()

    if (
        not expected_symbol
        or str(lifecycle["symbol"]).upper().strip()
        != expected_symbol
    ):
        raise ActiveTradeRecoveryError(
            "FAIL-CLOSED: Active lifecycle symbol mismatch"
        )

    position_direction = str(
        getattr(position, "position", "NONE")
    ).upper().strip()

    if position_direction not in {"LONG", "SHORT"}:
        raise ActiveTradeRecoveryError(
            "FAIL-CLOSED: Invalid active lifecycle position"
        )

    if (
        str(lifecycle["position"]).upper().strip()
        != position_direction
    ):
        raise ActiveTradeRecoveryError(
            "FAIL-CLOSED: Active lifecycle position mismatch"
        )

    try:
        current_stop = float(
            getattr(position, "stop_loss", 0.0)
        )
    except (TypeError, ValueError) as exc:
        raise ActiveTradeRecoveryError(
            "FAIL-CLOSED: Invalid active lifecycle current stop"
        ) from exc

    if (
        not math.isfinite(current_stop)
        or current_stop <= 0
    ):
        raise ActiveTradeRecoveryError(
            "FAIL-CLOSED: Invalid active lifecycle current stop"
        )

    try:
        manager_state = manager.snapshot()
    except Exception as exc:
        raise ActiveTradeRecoveryError(
            "FAIL-CLOSED: Unable to snapshot TradeManager lifecycle"
        ) from exc

    if not isinstance(manager_state, dict):
        raise ActiveTradeRecoveryError(
            "FAIL-CLOSED: Invalid TradeManager lifecycle snapshot"
        )

    lifecycle_flags = (
        "position_open",
        "trade_closed",
        "break_even",
        "trailing",
        "tp1_hit",
        "tp2_hit",
    )

    for field in lifecycle_flags:
        if not isinstance(
            manager_state.get(field),
            bool,
        ):
            raise ActiveTradeRecoveryError(
                "FAIL-CLOSED: Invalid TradeManager lifecycle flag: "
                f"{field}"
            )

    if manager_state["position_open"] is not True:
        raise ActiveTradeRecoveryError(
            "FAIL-CLOSED: Non-terminal lifecycle has inactive manager"
        )

    if manager_state["trade_closed"] is not False:
        raise ActiveTradeRecoveryError(
            "FAIL-CLOSED: Non-terminal lifecycle is marked closed"
        )

    # R56-POS-26: validate the current stop against the canonical
    # execution plan before allowing a new durable lifecycle revision.
    if not isinstance(plan, dict):
        raise ActiveTradeRecoveryError(
            "FAIL-CLOSED: Missing canonical active trade plan"
        )

    expected_plan_direction = {
        "LONG": "BUY",
        "SHORT": "SELL",
    }[position_direction]

    plan_direction = str(
        plan.get("Direction", "")
    ).upper().strip()

    if plan_direction != expected_plan_direction:
        raise ActiveTradeRecoveryError(
            "FAIL-CLOSED: Active lifecycle plan direction mismatch"
        )

    entry = _positive_float(
        plan.get("Entry"),
        "plan entry",
    )

    original_stop = _positive_float(
        plan.get("StopLoss"),
        "plan stop loss",
    )

    tp1_hit = manager_state["tp1_hit"]
    tp2_hit = manager_state["tp2_hit"]
    break_even = manager_state["break_even"]
    trailing = manager_state["trailing"]

    if tp2_hit and not tp1_hit:
        raise ActiveTradeRecoveryError(
            "FAIL-CLOSED: Durable TP2 lifecycle precedes TP1"
        )

    if break_even != tp1_hit:
        raise ActiveTradeRecoveryError(
            "FAIL-CLOSED: Durable break-even/TP1 lifecycle mismatch"
        )

    if trailing != tp2_hit:
        raise ActiveTradeRecoveryError(
            "FAIL-CLOSED: Durable trailing/TP2 lifecycle mismatch"
        )

    # R56-POS-26: active-management lifecycle is forward-only.
    # A durable revision must never erase a previously reached milestone.
    monotonic_flags = (
        "tp1_hit",
        "tp2_hit",
        "break_even",
        "trailing",
    )

    current_flags = {
        "tp1_hit": tp1_hit,
        "tp2_hit": tp2_hit,
        "break_even": break_even,
        "trailing": trailing,
    }

    for field in monotonic_flags:
        if bool(lifecycle[field]) and not current_flags[field]:
            raise ActiveTradeRecoveryError(
                "FAIL-CLOSED: Active lifecycle flag regressed: "
                f"{field}"
            )

    # R56-POS-26: once durable trailing is active, the current stop
    # must never move backward relative to the previous durable revision.
    previous_stop = _positive_float(
        lifecycle["current_stop"],
        "previous durable current stop",
    )

    if bool(lifecycle["trailing"]) and trailing:
        if position_direction == "LONG":
            if current_stop < previous_stop:
                raise ActiveTradeRecoveryError(
                    "FAIL-CLOSED: LONG trailing stop regressed "
                    "from previous durable revision"
                )
        else:
            if current_stop > previous_stop:
                raise ActiveTradeRecoveryError(
                    "FAIL-CLOSED: SHORT trailing stop regressed "
                    "from previous durable revision"
                )

    if not tp1_hit:
        if not _same(current_stop, original_stop):
            raise ActiveTradeRecoveryError(
                "FAIL-CLOSED: Pre-TP1 current stop is inconsistent"
            )
    elif not tp2_hit:
        if not _same(current_stop, entry):
            raise ActiveTradeRecoveryError(
                "FAIL-CLOSED: Break-even current stop is inconsistent"
            )
    else:
        if position_direction == "LONG":
            if current_stop < entry:
                raise ActiveTradeRecoveryError(
                    "FAIL-CLOSED: LONG trailing stop regressed below entry"
                )
        else:
            if current_stop > entry:
                raise ActiveTradeRecoveryError(
                    "FAIL-CLOSED: SHORT trailing stop regressed above entry"
                )

    desired = {
        "current_stop": current_stop,
        "tp1_hit": manager_state["tp1_hit"],
        "tp2_hit": manager_state["tp2_hit"],
        "break_even": manager_state["break_even"],
        "trailing": manager_state["trailing"],
    }

    unchanged = (
        math.isclose(
            float(lifecycle["current_stop"]),
            current_stop,
            rel_tol=0.0,
            abs_tol=1e-8,
        )
        and bool(lifecycle["tp1_hit"]) == desired["tp1_hit"]
        and bool(lifecycle["tp2_hit"]) == desired["tp2_hit"]
        and bool(lifecycle["break_even"]) == desired["break_even"]
        and bool(lifecycle["trailing"]) == desired["trailing"]
    )

    if unchanged:
        return int(lifecycle["revision"])

    current_revision = int(
        lifecycle["revision"]
    )

    update_active_trade_lifecycle(
        trade_uuid=trade_uuid.strip(),
        authorization_id=str(
            lifecycle["authorization_id"]
        ).strip(),
        symbol=expected_symbol,
        position=position_direction,
        current_stop=desired["current_stop"],
        tp1_hit=desired["tp1_hit"],
        tp2_hit=desired["tp2_hit"],
        break_even=desired["break_even"],
        trailing=desired["trailing"],
        revision=current_revision + 1,
        expected_revision=current_revision,
        updated_at=datetime.utcnow().isoformat(),
    )

    return current_revision + 1
