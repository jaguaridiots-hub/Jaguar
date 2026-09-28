"""Fail-closed reconstruction of an already-open PAPER trade."""

import math

from research.database import get_connection


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

        entry = _positive_float(
            getattr(position, "entry", 0.0),
            "entry",
        )

        trade_entry = _positive_float(
            trade.get("entry_price"),
            "trade entry",
        )

        if not _same(entry, trade_entry):
            raise ActiveTradeRecoveryError(
                "FAIL-CLOSED: Position entry conflicts with durable trade"
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

        if not {0, 1, 2}.issubset(targets):
            raise ActiveTradeRecoveryError(
                "FAIL-CLOSED: Durable TP1/TP2/TP3 contract is incomplete"
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
            "Entry": entry,
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
