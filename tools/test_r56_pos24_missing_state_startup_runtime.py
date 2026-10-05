"""R56-POS-24G actual main.py missing-state startup branch witness."""

import ast
from pathlib import Path
from types import SimpleNamespace
import tempfile

import engine.state_manager as sm
import intelligence.paper_post_fill as pp
import research.database as db

from engine.active_trade_recovery import (
    recover_active_trade_from_durable_lifecycle,
)
from engine.position_manager import PositionManager
from engine.trade_manager import TradeManager
from research.recorder import record_trade_open


MAIN_SOURCE = Path("main.py").read_text()


def make_state(auth, trade_uuid):
    return SimpleNamespace(
        symbol="BTCUSDT",
        interval="15m",
        mode="PAPER",
        price=101.0,
        high=102.0,
        low=99.0,
        volume=1000.0,
        run_id="R56-POS24-MISSING-STATE",
        execution={
            "authorization_id": auth,
            "client_order_id": "CLIENT-R56-POS24-MISSING",
            "trade_uuid": trade_uuid,
            "symbol": "BTCUSDT",
            "decision": "ENTER_LONG",
            "entry": 100.0,
            "stop_loss": 95.0,
            "targets": [105.0, 110.0, 115.0],
            "position_size": 2.0,
            "risk_amount": 10.0,
            "mode": "PAPER",
            "fill_price": 101.0,
            "filled_quantity": 2.0,
            "order_status": "FILLED",
        },
        trade={
            "entry": 100.0,
            "stop_loss": 95.0,
            "targets": [105.0, 110.0, 115.0],
        },
        trade_plan={},
        idm={
            "decision": "LONG",
            "confidence": 90.0,
            "score": 95.0,
        },
        master_decision={},
        ai_brain={"score": 90.0},
        probability={"score": 90.0},
        risk={"approved": True},
        trade_validator={"validation_score": 100.0},
        _decision_weights={},
        brain_explain={"contributions": []},
        regime={},
        market={
            "regime_result": {},
            "liquidity_result": {},
            "structural_results": {
                "fvg": {},
            },
        },
        mtf={},
        smc={},
        liquidity={},
        orderflow={},
    )


def seed_durable_trade():
    auth = "AUTH-R56-POS24-MISSING"
    trade_uuid = "TRADE-R56-POS24-MISSING"

    state = make_state(auth, trade_uuid)

    db.insert_execution_intent(
        {
            "authorization_id": auth,
            "trade_uuid": trade_uuid,
            "client_order_id": "CLIENT-R56-POS24-MISSING",
            "broker_order_id": None,
            "symbol": "BTCUSDT",
            "timeframe": "15m",
            "mode": "PAPER",
            "decision": "LONG",
            "quantity": 2.0,
            "requested_price": 100.0,
            "stop_loss": 95.0,
            "take_profit": 105.0,
            "run_id": state.run_id,
            "status": "AUTHORIZED",
            "created_at": "2026-09-29T00:00:00",
            "updated_at": "2026-09-29T00:00:00",
        }
    )

    db.update_execution_intent(
        auth,
        broker_order_id="PAPER-R56-POS24-MISSING",
        status="SUBMITTED",
    )

    recorded = record_trade_open(
        state,
        run_id=state.run_id,
        entry_time="2026-09-29T00:00:00",
        trade_uuid=trade_uuid,
        authorization_id=auth,
    )

    assert recorded == trade_uuid

    pp._persist_paper_durable_lifecycle(
        execution=dict(state.execution),
        execution_result={
            "requested_quantity": 2.0,
            "filled_quantity": 2.0,
            "fill_price": 101.0,
            "remaining_quantity": 0.0,
            "order_status": "FILLED",
            "order": {
                "authorization_id": auth,
                "client_order_id": "CLIENT-R56-POS24-MISSING",
                "broker_order_id": "PAPER-R56-POS24-MISSING",
                "symbol": "BTCUSDT",
                "side": "BUY",
                "requested_qty": 2.0,
                "filled_qty": 2.0,
                "remaining_qty": 0.0,
                "average_fill_price": 101.0,
                "status": "FILLED",
            },
            "position_reconciliation": {
                "authorization_id": auth,
                "symbol": "BTCUSDT",
                "quantity": 2.0,
                "reconciled": True,
            },
            "protection": {
                "authorization_id": auth,
                "quantity": 2.0,
                "stop_loss": 95.0,
                "targets": [105.0, 110.0, 115.0],
            },
            "protection_reconciliation": {
                "reconciled": True,
            },
        },
        authorization_id=auth,
        filled_quantity=2.0,
        authorized_stop=95.0,
        authorized_targets=[105.0, 110.0, 115.0],
    )

    pp._persist_initial_active_trade_lifecycle(
        trade_uuid=trade_uuid,
        authorization_id=auth,
        direction="BUY",
        authorized_stop=95.0,
        SYMBOL="BTCUSDT",
    )

    # Advance active management to a durable TP1 state.
    db.update_active_trade_lifecycle(
        trade_uuid,
        authorization_id=auth,
        symbol="BTCUSDT",
        position="LONG",
        current_stop=101.0,
        tp1_hit=True,
        tp2_hit=False,
        break_even=True,
        trailing=False,
        revision=2,
        expected_revision=1,
        updated_at="2026-09-29T00:02:00",
    )

    return auth, trade_uuid


def find_missing_state_node():
    tree = ast.parse(MAIN_SOURCE)

    for node in tree.body:
        if not isinstance(node, ast.If):
            continue

        test = node.test

        # Canonical production startup branch:
        # if not position_loaded and runtime_execution_mode == "PAPER":
        if not (
            isinstance(test, ast.BoolOp)
            and isinstance(test.op, ast.And)
            and len(test.values) == 2
        ):
            continue

        first, second = test.values

        first_matches = (
            isinstance(first, ast.UnaryOp)
            and isinstance(first.op, ast.Not)
            and isinstance(first.operand, ast.Name)
            and first.operand.id == "position_loaded"
        )

        second_matches = (
            isinstance(second, ast.Compare)
            and len(second.ops) == 1
            and isinstance(second.ops[0], ast.Eq)
            and isinstance(second.left, ast.Name)
            and second.left.id == "runtime_execution_mode"
            and len(second.comparators) == 1
            and isinstance(second.comparators[0], ast.Constant)
            and second.comparators[0].value == "PAPER"
        )

        if first_matches and second_matches:
            return node

    raise AssertionError(
        "Actual PAPER startup `if not position_loaded and "
        "runtime_execution_mode == 'PAPER'` node not found"
    )


def main():
    with tempfile.TemporaryDirectory(
        dir=".jaguar_audit",
        prefix="r56-pos24-missing-startup-",
    ) as td:

        original_db = db.DB_PATH
        original_file = sm.FILE

        db.DB_PATH = str(
            Path(td) / "missing-startup.db"
        )

        # Explicitly absent local cache.
        sm.FILE = str(
            Path(td) / "trade_state.json"
        )

        try:
            db.init_db()

            auth, trade_uuid = seed_durable_trade()

            assert not Path(sm.FILE).exists()

            position = PositionManager()
            manager = TradeManager()
            state = SimpleNamespace(
                _trade_id=None
            )

            execution_calls = {
                "recovery": 0,
                "intent": 0,
                "broker": 0,
            }

            real_recovery = (
                recover_active_trade_from_durable_lifecycle
            )

            def recovery_spy(
                *,
                position,
                manager,
                symbol,
            ):
                execution_calls["recovery"] += 1

                return real_recovery(
                    position=position,
                    manager=manager,
                    symbol=symbol,
                )

            def forbidden_execution():
                raise AssertionError(
                    "FAIL: execution path reached during recovery"
                )

            node = find_missing_state_node()

            runtime_globals = {
                "position_loaded": False,
                "runtime_execution_mode": "PAPER",
                "position": position,
                "manager": manager,
                "state": state,
                "SYMBOL": "BTCUSDT",
                "recover_active_trade_from_durable_lifecycle": (
                    recovery_spy
                ),
                "assert_no_orphan_durable_trade": (
                    lambda symbol: forbidden_execution()
                ),
                "print": print,
            }

            compiled = compile(
                ast.Module(
                    body=[node],
                    type_ignores=[],
                ),
                "main.py",
                "exec",
            )

            exec(
                compiled,
                runtime_globals,
            )

            assert execution_calls["recovery"] == 1

            assert position.position == "LONG"
            assert position.trade_uuid == trade_uuid

            assert position.entry == 101.0
            assert position.stop_loss == 101.0
            assert position.take_profit == 105.0
            assert position.position_size == 2.0
            assert position.initial_risk == 12.0

            manager_state = manager.snapshot()

            assert manager_state["position_open"] is True
            assert manager_state["trade_closed"] is False
            assert manager_state["tp1_hit"] is True
            assert manager_state["tp2_hit"] is False
            assert manager_state["break_even"] is True
            assert manager_state["trailing"] is False

            assert state._trade_id == trade_uuid

            plan = runtime_globals["plan"]

            assert plan["TradeUUID"] == trade_uuid
            assert plan["Direction"] == "BUY"
            assert plan["Entry"] == 101.0
            assert plan["TP1"] == 105.0

            lifecycle = dict(
                db.get_active_trade_lifecycle(
                    trade_uuid
                )
            )

            assert lifecycle["revision"] == 2
            assert lifecycle["current_stop"] == 101.0

            assert (
                execution_calls["intent"]
                == 0
            )
            assert (
                execution_calls["broker"]
                == 0
            )

            print(
                "R56_POS24_ACTUAL_MAIN_MISSING_STATE_BRANCH: PASS"
            )

            print(
                "R56_POS24_MISSING_STATE_RECONSTRUCTS_EXISTING_PAPER_TRADE: PASS"
            )

            print(
                "R56_POS24_MISSING_STATE_NO_REENTRY: PASS"
            )

            print(
                "R56_POS24_MISSING_STATE_NO_EXECUTION: PASS"
            )

        finally:
            sm.FILE = original_file
            db.DB_PATH = original_db


if __name__ == "__main__":
    main()
