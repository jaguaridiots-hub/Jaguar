"""Jaguar Quant X
PAPER post-fill lifecycle.

This module is an extracted transaction boundary from the
pre-B3-B main.py source. It contains no broker submission path.
"""

from datetime import datetime

from engine.state_manager import save, clear
from research.database import update_execution_intent
from research.recorder import record_trade_open


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
            update_execution_intent(authorization_id, status='RECONCILED')
        except Exception as intent_error:
            raise RuntimeError('FAIL-CLOSED: Execution reconciliation persistence failed') from intent_error
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
            update_execution_intent(authorization_id, status='RECONCILED')
        except Exception as intent_error:
            raise RuntimeError('FAIL-CLOSED: Execution reconciliation persistence failed') from intent_error
        manager.activate()
