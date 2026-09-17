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

    if float(execution_result.get("remaining_quantity", 0.0) or 0.0) != 0.0:
        raise RuntimeError(
            "FAIL-CLOSED: PAPER execution has remaining quantity"
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
    filled_quantity = float(execution_result.get('filled_quantity', 0.0) or 0.0)
    fill_price = float(execution_result.get('fill_price', 0.0) or 0.0)
    if filled_quantity <= 0 or fill_price <= 0:
        try:
            rollback_execution_if_pre_submission(execution_result)
        except Exception as rollback_error:
            raise RuntimeError('FAIL-CLOSED: Invalid broker fill AND execution rollback failed') from rollback_error
        raise RuntimeError('FAIL-CLOSED: Invalid broker fill')
    if isinstance(getattr(state, 'execution', None), dict):
        state.execution['authorization_id'] = authorization_id
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
    if 'BUY' in direction:
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
        if not save(position, SYMBOL):
            db_error = None
            execution_error = None
            try:
                preserve_trade_for_recovery(trade_uuid)
            except Exception as rollback_error:
                db_error = rollback_error
            try:
                rollback_execution_if_pre_submission(execution_result)
            except Exception as rollback_error:
                execution_error = rollback_error
            position.close_trade()
            state._trade_id = None
            clear()
            if db_error is not None and execution_error is not None:
                raise RuntimeError('FAIL-CLOSED: Position persistence failed; trade evidence preservation AND broker compensation were unavailable') from execution_error
            if db_error is not None:
                raise RuntimeError('FAIL-CLOSED: Position persistence failed AND trade evidence preservation failed') from db_error
            if execution_error is not None:
                raise RuntimeError('FAIL-CLOSED: Position persistence failed AND execution rollback failed') from execution_error
            raise RuntimeError('FAIL-CLOSED: Position persistence failed; DB trade and broker execution preserved for recovery')
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
        manager.activate()
    elif 'SELL' in direction:
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
        if not save(position, SYMBOL):
            db_error = None
            execution_error = None
            try:
                preserve_trade_for_recovery(trade_uuid)
            except Exception as rollback_error:
                db_error = rollback_error
            try:
                rollback_execution_if_pre_submission(execution_result)
            except Exception as rollback_error:
                execution_error = rollback_error
            position.close_trade()
            state._trade_id = None
            clear()
            if db_error is not None and execution_error is not None:
                raise RuntimeError('FAIL-CLOSED: Position persistence failed; trade evidence preservation AND broker compensation were unavailable') from execution_error
            if db_error is not None:
                raise RuntimeError('FAIL-CLOSED: Position persistence failed AND trade evidence preservation failed') from db_error
            if execution_error is not None:
                raise RuntimeError('FAIL-CLOSED: Position persistence failed AND execution rollback failed') from execution_error
            raise RuntimeError('FAIL-CLOSED: Position persistence failed; DB trade and broker execution preserved for recovery')
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
        manager.activate()
