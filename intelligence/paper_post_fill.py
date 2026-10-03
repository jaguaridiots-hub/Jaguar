"""Jaguar Quant X
PAPER post-fill lifecycle.

This module is an extracted transaction boundary from the
pre-B3-B main.py source. It contains no broker submission path.
"""

from datetime import datetime

from engine.state_manager import save, clear
from research.database import (
    insert_execution_protection,
    get_execution_intent,
    get_execution_protection,
    list_execution_protections,
    update_execution_intent,
    update_execution_protection,
)
from research.recorder import record_trade_open


def _persist_paper_durable_lifecycle(
    *,
    execution,
    execution_result,
    authorization_id,
    filled_quantity,
    authorized_stop,
    authorized_targets,
):
    """Persist the already-completed PAPER broker lifecycle exactly once.

    This function performs no broker submission and no broker mutation.
    It records the durable parent/protection lifecycle from the authoritative
    Paper execution result.
    """
    if not isinstance(execution, dict):
        raise RuntimeError(
            "FAIL-CLOSED: Invalid PAPER execution contract"
        )
    if not isinstance(execution_result, dict):
        raise RuntimeError(
            "FAIL-CLOSED: Invalid PAPER execution result"
        )

    intent = get_execution_intent(authorization_id)
    if intent is None:
        raise RuntimeError(
            "FAIL-CLOSED: PAPER execution intent not found"
        )

    current_status = str(intent["status"]).strip().upper()

    if current_status not in {
        "SUBMITTED",
        "FILLED",
        "POSITION_RECONCILING",
        "PROTECTION_PENDING",
        "RECONCILED",
    }:
        raise RuntimeError(
            "FAIL-CLOSED: Invalid PAPER durable lifecycle state: "
            f"{current_status}"
        )

    if current_status == "RECONCILED":
        return

    order = execution_result.get("order") or {}
    if not isinstance(order, dict):
        raise RuntimeError(
            "FAIL-CLOSED: PAPER execution returned invalid order evidence"
        )

    if (
        str(order.get("authorization_id", "")).strip()
        != authorization_id
    ):
        raise RuntimeError(
            "FAIL-CLOSED: PAPER order authorization identity mismatch"
        )

    if (
        str(order.get("status", "")).strip().upper()
        != "FILLED"
    ):
        raise RuntimeError(
            "FAIL-CLOSED: PAPER execution did not reach FILLED"
        )

    remaining_quantity = float(
        execution_result.get("remaining_quantity", 0.0) or 0.0
    )

    if remaining_quantity != 0.0:
        raise RuntimeError(
            "FAIL-CLOSED: PAPER execution has remaining quantity"
        )

    # R56-POS-31: durable reconciliation requires a complete fill
    # of the exact quantity authorized by the durable execution intent.
    try:
        intent_quantity = float(
            intent["quantity"]
        )
        result_requested_quantity = float(
            execution_result.get(
                "requested_quantity",
                0.0,
            ) or 0.0
        )
        result_filled_quantity = float(
            execution_result.get(
                "filled_quantity",
                0.0,
            ) or 0.0
        )
        order_requested_quantity = float(
            order.get(
                "requested_qty",
                0.0,
            ) or 0.0
        )
        order_filled_quantity = float(
            order.get(
                "filled_qty",
                0.0,
            ) or 0.0
        )
        lifecycle_filled_quantity = float(
            filled_quantity
        )
    except (TypeError, ValueError):
        raise RuntimeError(
            "FAIL-CLOSED: PAPER execution quantity evidence invalid"
        )

    if (
        intent_quantity <= 0
        or result_requested_quantity <= 0
        or result_filled_quantity <= 0
        or order_requested_quantity <= 0
        or order_filled_quantity <= 0
        or lifecycle_filled_quantity <= 0
        or intent_quantity != result_requested_quantity
        or intent_quantity != result_filled_quantity
        or intent_quantity != order_requested_quantity
        or intent_quantity != order_filled_quantity
        or intent_quantity != lifecycle_filled_quantity
        or result_requested_quantity != result_filled_quantity
        or order_requested_quantity != order_filled_quantity
    ):
        raise RuntimeError(
            "FAIL-CLOSED: PAPER execution quantity authority mismatch"
        )

    if current_status == "SUBMITTED":
        update_execution_intent(
            authorization_id,
            status="FILLED",
        )
        current_status = "FILLED"

    position_reconciliation = (
        execution_result.get("position_reconciliation") or {}
    )
    if not isinstance(position_reconciliation, dict):
        raise RuntimeError(
            "FAIL-CLOSED: Invalid PAPER position reconciliation evidence"
        )
    if position_reconciliation.get("reconciled") is not True:
        raise RuntimeError(
            "FAIL-CLOSED: PAPER position reconciliation is not verified"
        )

    if current_status == "FILLED":
        update_execution_intent(
            authorization_id,
            status="POSITION_RECONCILING",
        )
        current_status = "POSITION_RECONCILING"

    normalized_stop = float(authorized_stop)
    normalized_targets = [
        float(target)
        for target in authorized_targets
    ]

    if normalized_stop <= 0 or not normalized_targets:
        raise RuntimeError(
            "FAIL-CLOSED: Invalid PAPER protection geometry"
        )

    protection = execution_result.get("protection") or {}
    if not isinstance(protection, dict):
        raise RuntimeError(
            "FAIL-CLOSED: Invalid PAPER protection evidence"
        )

    if (
        str(protection.get("authorization_id", "")).strip()
        != authorization_id
    ):
        raise RuntimeError(
            "FAIL-CLOSED: PAPER protection authorization identity mismatch"
        )

    if float(protection.get("quantity", 0.0) or 0.0) != float(filled_quantity):
        raise RuntimeError(
            "FAIL-CLOSED: PAPER protection quantity mismatch"
        )

    if float(protection.get("stop_loss", 0.0) or 0.0) != normalized_stop:
        raise RuntimeError(
            "FAIL-CLOSED: PAPER protection stop mismatch"
        )

    observed_targets = [
        float(target)
        for target in (protection.get("targets") or [])
    ]
    if observed_targets != normalized_targets:
        raise RuntimeError(
            "FAIL-CLOSED: PAPER protection targets mismatch"
        )

    if current_status == "POSITION_RECONCILING":
        now = datetime.utcnow().isoformat()

        protection_specs = [
            (
                f"{authorization_id}:PROTECTION:SL",
                "STOP_LOSS",
                None,
                normalized_stop,
            ),
        ]

        for index, target in enumerate(normalized_targets):
            protection_specs.append(
                (
                    f"{authorization_id}:PROTECTION:TP{index + 1}",
                    "TAKE_PROFIT",
                    index,
                    target,
                )
            )

        for (
            protection_id,
            protection_type,
            target_index,
            requested_price,
        ) in protection_specs:
            existing = get_execution_protection(protection_id)

            if existing is None:
                insert_execution_protection(
                    {
                        "protection_id": protection_id,
                        "authorization_id": authorization_id,
                        "protection_type": protection_type,
                        "target_index": target_index,
                        "broker_order_id": None,
                        "requested_qty": float(filled_quantity),
                        "verified_qty": None,
                        "requested_price": requested_price,
                        "verified_price": None,
                        "status": "PENDING",
                        "created_at": now,
                        "updated_at": now,
                    }
                )
            else:
                existing = dict(existing)
                if (
                    str(existing.get("authorization_id", "")).strip()
                    != authorization_id
                    or str(existing.get("protection_type", "")).strip().upper()
                    != protection_type
                    or float(existing.get("requested_qty", 0.0))
                    != float(filled_quantity)
                    or float(existing.get("requested_price", 0.0))
                    != requested_price
                ):
                    raise RuntimeError(
                        "FAIL-CLOSED: PAPER durable protection identity mismatch"
                    )

        update_execution_intent(
            authorization_id,
            status="PROTECTION_PENDING",
        )
        current_status = "PROTECTION_PENDING"

    protection_reconciliation = (
        execution_result.get("protection_reconciliation") or {}
    )
    if not isinstance(protection_reconciliation, dict):
        raise RuntimeError(
            "FAIL-CLOSED: Invalid PAPER protection reconciliation evidence"
        )

    if protection_reconciliation.get("reconciled") is not True:
        raise RuntimeError(
            "FAIL-CLOSED: PAPER protection reconciliation is not verified"
        )

    if current_status == "PROTECTION_PENDING":
        durable_protections = [
            dict(row)
            for row in list_execution_protections(authorization_id)
        ]

        expected_count = 1 + len(normalized_targets)
        if len(durable_protections) != expected_count:
            raise RuntimeError(
                "FAIL-CLOSED: PAPER durable protection count mismatch"
            )

        for durable in durable_protections:
            if str(durable["status"]).strip().upper() == "PENDING":
                update_execution_protection(
                    durable["protection_id"],
                    verified_qty=float(filled_quantity),
                    verified_price=float(durable["requested_price"]),
                    status="VERIFIED",
                )
            elif str(durable["status"]).strip().upper() != "VERIFIED":
                raise RuntimeError(
                    "FAIL-CLOSED: Invalid PAPER protection lifecycle state"
                )

        update_execution_intent(
            authorization_id,
            status="RECONCILED",
        )



def _persist_initial_active_trade_lifecycle(
    *,
    trade_uuid,
    authorization_id,
    direction,
    authorized_stop,
    SYMBOL,
):
    """Create the first durable active-management snapshot."""

    if (
        not isinstance(trade_uuid, str)
        or not trade_uuid.strip()
    ):
        raise RuntimeError(
            "FAIL-CLOSED: Invalid trade UUID for active lifecycle"
        )

    if (
        not isinstance(authorization_id, str)
        or not authorization_id.strip()
    ):
        raise RuntimeError(
            "FAIL-CLOSED: Invalid authorization ID for active lifecycle"
        )

    symbol = str(
        SYMBOL or ""
    ).upper().strip()

    if not symbol:
        raise RuntimeError(
            "FAIL-CLOSED: Invalid symbol for active lifecycle"
        )

    normalized_direction = str(
        direction or ""
    ).upper().strip()

    position = {
        "BUY": "LONG",
        "SELL": "SHORT",
    }.get(
        normalized_direction
    )

    if position is None:
        raise RuntimeError(
            "FAIL-CLOSED: Invalid execution direction for active lifecycle"
        )

    try:
        current_stop = float(authorized_stop)
    except (TypeError, ValueError) as exc:
        raise RuntimeError(
            "FAIL-CLOSED: Invalid initial active lifecycle stop"
        ) from exc

    if (
        not current_stop > 0
        or current_stop != current_stop
        or current_stop in (
            float("inf"),
            float("-inf"),
        )
    ):
        raise RuntimeError(
            "FAIL-CLOSED: Invalid initial active lifecycle stop"
        )

    from research.database import insert_active_trade_lifecycle

    now = datetime.utcnow().isoformat()

    insert_active_trade_lifecycle(
        {
            "trade_uuid": trade_uuid.strip(),
            "authorization_id": authorization_id.strip(),
            "symbol": symbol,
            "position": position,
            "current_stop": current_stop,
            "tp1_hit": False,
            "tp2_hit": False,
            "break_even": False,
            "trailing": False,
            "trade_closed": False,
            "revision": 1,
            "created_at": now,
            "updated_at": now,
        }
    )



def execute_paper_post_fill(
    *,
    execution,
    execution_result,
    authorization_id,
    trade_uuid,
    authorized_stop,
    authorized_targets,
    direction,
    state,
    position,
    manager,
    journal,
    plan,
    rollback_execution_if_pre_submission,
    preserve_trade_for_recovery,
    SYMBOL,
    TIMEFRAME,
):
    normalized_direction = str(
        direction or ""
    ).upper().strip()

    if normalized_direction not in {"BUY", "SELL"}:
        raise RuntimeError(
            "FAIL-CLOSED: Invalid PAPER execution direction"
        )

    filled_quantity = float(execution_result.get('filled_quantity', 0.0) or 0.0)
    fill_price = float(execution_result.get('fill_price', 0.0) or 0.0)
    if filled_quantity <= 0 or fill_price <= 0:
        try:
            rollback_execution_if_pre_submission(execution_result)
        except Exception as rollback_error:
            raise RuntimeError('FAIL-CLOSED: Invalid broker fill AND execution rollback failed') from rollback_error
        raise RuntimeError('FAIL-CLOSED: Invalid broker fill')
    if isinstance(getattr(state, 'execution', None), dict):
        state.execution['fill_price'] = fill_price
        state.execution['filled_quantity'] = filled_quantity
        state.execution['order_status'] = execution_result.get('order_status')
    position_size = filled_quantity
    initial_risk = abs(fill_price - float(authorized_stop or 0.0)) * position_size
    if initial_risk <= 0:
        try:
            rollback_execution_if_pre_submission(execution_result)
        except Exception as rollback_error:
            raise RuntimeError('FAIL-CLOSED: Invalid filled-trade risk AND execution rollback failed') from rollback_error
        raise RuntimeError('FAIL-CLOSED: Invalid filled-trade risk')
    if normalized_direction == 'BUY':
        if position.position != 'NONE':
            raise RuntimeError('FAIL-CLOSED: Position already active')
        try:
            position.open_trade('LONG', fill_price, authorized_stop, authorized_targets[0], position_size=position_size, initial_risk=initial_risk)
        except Exception as position_error:
            try:
                rollback_execution_if_pre_submission(execution_result)
            except Exception as rollback_error:
                position.close_trade()
                state._trade_id = None
                clear()
                raise RuntimeError('FAIL-CLOSED: Position open failed AND execution rollback failed') from rollback_error
            position.close_trade()
            state._trade_id = None
            clear()
            raise RuntimeError('FAIL-CLOSED: Position open failed; broker execution preserved for recovery') from position_error
        try:
            recorded_uuid = record_trade_open(state, run_id=getattr(state, 'run_id', None), entry_time=getattr(state, '_candle_time', None), trade_uuid=trade_uuid, authorization_id=authorization_id)
        except Exception as trade_error:
            try:
                rollback_execution_if_pre_submission(execution_result)
            except Exception as rollback_error:
                position.close_trade()
                state._trade_id = None
                clear()
                raise RuntimeError('FAIL-CLOSED: Trade persistence failed AND execution rollback failed') from rollback_error
            position.close_trade()
            state._trade_id = None
            clear()
            raise RuntimeError('FAIL-CLOSED: Trade persistence failed; broker execution preserved for recovery') from trade_error
        if recorded_uuid != trade_uuid:
            try:
                preserve_trade_for_recovery(trade_uuid)
            except Exception as rollback_error:
                position.close_trade()
                state._trade_id = None
                clear()
                raise RuntimeError('FAIL-CLOSED: Trade identity mismatch AND trade evidence preservation failed') from rollback_error
            position.close_trade()
            state._trade_id = None
            clear()
            try:
                rollback_execution_if_pre_submission(execution_result)
            except Exception as execution_rollback_error:
                position.close_trade()
                state._trade_id = None
                clear()
                raise RuntimeError('FAIL-CLOSED: Trade identity mismatch AND execution rollback failed') from execution_rollback_error
            position.close_trade()
            state._trade_id = None
            clear()
            raise RuntimeError('FAIL-CLOSED: Trade identity mismatch; broker execution preserved for recovery')
        try:
            position.set_trade_uuid(trade_uuid)
        except Exception as identity_error:
            try:
                preserve_trade_for_recovery(trade_uuid)
            except Exception as delete_error:
                try:
                    rollback_execution_if_pre_submission(execution_result)
                except Exception as execution_rollback_error:
                    position.close_trade()
                    state._trade_id = None
                    clear()
                    raise RuntimeError('FAIL-CLOSED: Trade identity assignment failed, trade evidence preservation failed, AND broker execution remained non-reversible') from execution_rollback_error
                position.close_trade()
                state._trade_id = None
                clear()
                raise RuntimeError('FAIL-CLOSED: Trade identity assignment failed AND trade evidence preservation failed; broker execution preserved for recovery') from delete_error
            try:
                rollback_execution_if_pre_submission(execution_result)
            except Exception as execution_rollback_error:
                position.close_trade()
                state._trade_id = None
                clear()
                raise RuntimeError('FAIL-CLOSED: Trade identity assignment failed AND execution rollback failed') from execution_rollback_error
            position.close_trade()
            state._trade_id = None
            clear()
            raise RuntimeError('FAIL-CLOSED: Trade identity assignment failed; broker execution preserved for recovery') from identity_error
        state._trade_id = trade_uuid
        try:
            journal.save(state, plan)
        except Exception as journal_error:
            try:
                preserve_trade_for_recovery(trade_uuid)
            except Exception as rollback_error:
                try:
                    rollback_execution_if_pre_submission(execution_result)
                except Exception as execution_rollback_error:
                    position.close_trade()
                    state._trade_id = None
                    clear()
                    raise RuntimeError('FAIL-CLOSED: Journal persistence failed, trade evidence preservation failed, AND broker execution remained non-reversible') from execution_rollback_error
                position.close_trade()
                state._trade_id = None
                clear()
                raise RuntimeError('FAIL-CLOSED: Journal persistence failed AND trade evidence preservation failed; broker execution preserved for recovery') from rollback_error
            try:
                rollback_execution_if_pre_submission(execution_result)
            except Exception as execution_rollback_error:
                position.close_trade()
                state._trade_id = None
                clear()
                raise RuntimeError('FAIL-CLOSED: Journal persistence failed AND execution rollback failed') from execution_rollback_error
            position.close_trade()
            state._trade_id = None
            clear()
            raise RuntimeError('FAIL-CLOSED: Journal persistence failed; DB trade and broker execution preserved for recovery') from journal_error
        try:
            _persist_paper_durable_lifecycle(
                execution=execution,
                execution_result=execution_result,
                authorization_id=authorization_id,
                filled_quantity=filled_quantity,
                authorized_stop=authorized_stop,
                authorized_targets=authorized_targets,
            )
        except Exception as intent_error:
            raise RuntimeError(
                'FAIL-CLOSED: Execution reconciliation persistence failed'
            ) from intent_error

        try:
            _persist_initial_active_trade_lifecycle(
                trade_uuid=trade_uuid,
                authorization_id=authorization_id,
                direction=normalized_direction,
                authorized_stop=authorized_stop,
                SYMBOL=SYMBOL,
            )
        except Exception as lifecycle_error:
            raise RuntimeError(
                'FAIL-CLOSED: Initial active lifecycle persistence failed'
            ) from lifecycle_error

        manager.activate()
        if not save(position, SYMBOL, manager):
            raise RuntimeError(
                'FAIL-CLOSED: Active management-state persistence failed'
            )
    elif normalized_direction == 'SELL':
        if position.position != 'NONE':
            raise RuntimeError('FAIL-CLOSED: Position already active')
        try:
            position.open_trade('SHORT', fill_price, authorized_stop, authorized_targets[0], position_size=position_size, initial_risk=initial_risk)
        except Exception as position_error:
            try:
                rollback_execution_if_pre_submission(execution_result)
            except Exception as rollback_error:
                position.close_trade()
                state._trade_id = None
                clear()
                raise RuntimeError('FAIL-CLOSED: Position open failed AND execution rollback failed') from rollback_error
            position.close_trade()
            state._trade_id = None
            clear()
            raise RuntimeError('FAIL-CLOSED: Position open failed; broker execution preserved for recovery') from position_error
        try:
            recorded_uuid = record_trade_open(state, run_id=getattr(state, 'run_id', None), entry_time=getattr(state, '_candle_time', None), trade_uuid=trade_uuid, authorization_id=authorization_id)
        except Exception as trade_error:
            try:
                rollback_execution_if_pre_submission(execution_result)
            except Exception as rollback_error:
                position.close_trade()
                state._trade_id = None
                clear()
                raise RuntimeError('FAIL-CLOSED: Trade persistence failed AND execution rollback failed') from rollback_error
            position.close_trade()
            state._trade_id = None
            clear()
            raise RuntimeError('FAIL-CLOSED: Trade persistence failed; broker execution preserved for recovery') from trade_error
        if recorded_uuid != trade_uuid:
            try:
                preserve_trade_for_recovery(trade_uuid)
            except Exception as rollback_error:
                position.close_trade()
                state._trade_id = None
                clear()
                raise RuntimeError('FAIL-CLOSED: Trade identity mismatch AND trade evidence preservation failed') from rollback_error
            position.close_trade()
            state._trade_id = None
            clear()
            try:
                rollback_execution_if_pre_submission(execution_result)
            except Exception as execution_rollback_error:
                position.close_trade()
                state._trade_id = None
                clear()
                raise RuntimeError('FAIL-CLOSED: Trade identity mismatch AND execution rollback failed') from execution_rollback_error
            position.close_trade()
            state._trade_id = None
            clear()
            raise RuntimeError('FAIL-CLOSED: Trade identity mismatch; broker execution preserved for recovery')
        try:
            position.set_trade_uuid(trade_uuid)
        except Exception as identity_error:
            try:
                preserve_trade_for_recovery(trade_uuid)
            except Exception as delete_error:
                try:
                    rollback_execution_if_pre_submission(execution_result)
                except Exception as execution_rollback_error:
                    position.close_trade()
                    state._trade_id = None
                    clear()
                    raise RuntimeError('FAIL-CLOSED: Trade identity assignment failed, trade evidence preservation failed, AND broker execution remained non-reversible') from execution_rollback_error
                position.close_trade()
                state._trade_id = None
                clear()
                raise RuntimeError('FAIL-CLOSED: Trade identity assignment failed AND trade evidence preservation failed; broker execution preserved for recovery') from delete_error
            try:
                rollback_execution_if_pre_submission(execution_result)
            except Exception as execution_rollback_error:
                position.close_trade()
                state._trade_id = None
                clear()
                raise RuntimeError('FAIL-CLOSED: Trade identity assignment failed AND execution rollback failed') from execution_rollback_error
            position.close_trade()
            state._trade_id = None
            clear()
            raise RuntimeError('FAIL-CLOSED: Trade identity assignment failed; broker execution preserved for recovery') from identity_error
        state._trade_id = trade_uuid
        try:
            journal.save(state, plan)
        except Exception as journal_error:
            try:
                preserve_trade_for_recovery(trade_uuid)
            except Exception as rollback_error:
                try:
                    rollback_execution_if_pre_submission(execution_result)
                except Exception as execution_rollback_error:
                    position.close_trade()
                    state._trade_id = None
                    clear()
                    raise RuntimeError('FAIL-CLOSED: Journal persistence failed, trade evidence preservation failed, AND broker execution remained non-reversible') from execution_rollback_error
                position.close_trade()
                state._trade_id = None
                clear()
                raise RuntimeError('FAIL-CLOSED: Journal persistence failed AND trade evidence preservation failed; broker execution preserved for recovery') from rollback_error
            try:
                rollback_execution_if_pre_submission(execution_result)
            except Exception as execution_rollback_error:
                position.close_trade()
                state._trade_id = None
                clear()
                raise RuntimeError('FAIL-CLOSED: Journal persistence failed AND execution rollback failed') from execution_rollback_error
            position.close_trade()
            state._trade_id = None
            clear()
            raise RuntimeError('FAIL-CLOSED: Journal persistence failed; DB trade and broker execution preserved for recovery') from journal_error
        try:
            _persist_paper_durable_lifecycle(
                execution=execution,
                execution_result=execution_result,
                authorization_id=authorization_id,
                filled_quantity=filled_quantity,
                authorized_stop=authorized_stop,
                authorized_targets=authorized_targets,
            )
        except Exception as intent_error:
            raise RuntimeError(
                'FAIL-CLOSED: Execution reconciliation persistence failed'
            ) from intent_error

        try:
            _persist_initial_active_trade_lifecycle(
                trade_uuid=trade_uuid,
                authorization_id=authorization_id,
                direction=normalized_direction,
                authorized_stop=authorized_stop,
                SYMBOL=SYMBOL,
            )
        except Exception as lifecycle_error:
            raise RuntimeError(
                'FAIL-CLOSED: Initial active lifecycle persistence failed'
            ) from lifecycle_error

        manager.activate()
        if not save(position, SYMBOL, manager):
            raise RuntimeError(
                'FAIL-CLOSED: Active management-state persistence failed'
            )
