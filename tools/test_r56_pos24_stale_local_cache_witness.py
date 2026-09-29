"""R56-POS-24 witness for DB-vs-local-cache authority after a crash."""

import ast
from pathlib import Path
from types import SimpleNamespace
import tempfile

import research.database as db
import engine.state_manager as sm

from engine.position_manager import PositionManager
from engine.trade_manager import TradeManager
from engine.active_trade_recovery import (
    recover_active_trade_from_durable_lifecycle,
)
from research.recorder import record_trade_open
import intelligence.paper_post_fill as pp


def make_state(auth, trade_uuid):
    return SimpleNamespace(
        symbol="BTCUSDT",
        interval="15m",
        mode="PAPER",
        price=101.0,
        high=102.0,
        low=99.0,
        volume=1000.0,
        run_id="R56-POS24-STALE-CACHE",
        execution={
            "authorization_id": auth,
            "client_order_id": "CLIENT-R56-POS24-STALE",
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


def seed_trade():
    auth = "AUTH-R56-POS24-STALE"
    trade_uuid = "TRADE-R56-POS24-STALE"

    state = make_state(
        auth,
        trade_uuid,
    )

    db.insert_execution_intent(
        {
            "authorization_id": auth,
            "trade_uuid": trade_uuid,
            "client_order_id": "CLIENT-R56-POS24-STALE",
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
        broker_order_id="PAPER-R56-POS24-STALE",
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
            "filled_quantity": 2.0,
            "fill_price": 101.0,
            "remaining_quantity": 0.0,
            "order_status": "FILLED",
            "order": {
                "authorization_id": auth,
                "client_order_id": "CLIENT-R56-POS24-STALE",
                "broker_order_id": "PAPER-R56-POS24-STALE",
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

    return auth, trade_uuid


def main():
    with tempfile.TemporaryDirectory(
        dir=".jaguar_audit",
        prefix="r56-pos24-stale-",
    ) as td:

        original_db = db.DB_PATH
        original_file = sm.FILE

        db.DB_PATH = str(
            Path(td) / "stale-cache.db"
        )

        sm.FILE = str(
            Path(td) / "trade_state.json"
        )

        try:
            db.init_db()

            auth, trade_uuid = seed_trade()

            # Simulate revision-1 local cache.
            position = PositionManager()
            position.open_trade(
                "LONG",
                101.0,
                95.0,
                105.0,
                position_size=2.0,
                initial_risk=12.0,
            )
            position.set_trade_uuid(trade_uuid)

            manager = TradeManager()
            manager.activate()

            assert sm.save(
                position,
                "BTCUSDT",
                manager,
            )

            lifecycle_v1 = dict(
                db.get_active_trade_lifecycle(
                    trade_uuid
                )
            )

            assert lifecycle_v1["revision"] == 1
            assert lifecycle_v1["current_stop"] == 95.0
            assert lifecycle_v1["tp1_hit"] == 0

            # Simulated crash point:
            # DB advances, JSON remains revision 1.
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

            lifecycle_v2 = dict(
                db.get_active_trade_lifecycle(
                    trade_uuid
                )
            )

            assert lifecycle_v2["revision"] == 2
            assert lifecycle_v2["current_stop"] == 101.0
            assert lifecycle_v2["tp1_hit"] == 1

            # Fresh process objects load the stale local cache.
            restored_position = PositionManager()
            restored_manager = TradeManager()

            position_loaded = sm.load(
                restored_position,
                "BTCUSDT",
                restored_manager,
            )

            assert position_loaded is True

            print(
                "R56_POS24_STALE_JSON_CACHE_LOADS: PASS"
            )

            print(
                "R56_POS24_STALE_JSON_STOP:",
                restored_position.stop_loss,
            )

            print(
                "R56_POS24_STALE_MANAGER_TP1:",
                restored_manager.snapshot()["tp1_hit"],
            )

            assert restored_position.stop_loss == 95.0
            assert restored_manager.snapshot()["tp1_hit"] is False

            print(
                "R56_POS24_STALE_CACHE_FIXTURE_CONFIRMED: PASS"
            )

            # Execute the exact production `if position_loaded:` branch
            # from main.py without importing/running the whole application.
            main_source = Path("main.py").read_text()
            tree = ast.parse(main_source)

            startup_node = None

            for node in tree.body:
                if (
                    isinstance(node, ast.If)
                    and isinstance(node.test, ast.Name)
                    and node.test.id == "position_loaded"
                ):
                    startup_node = node
                    break

            assert startup_node is not None

            position_runtime = restored_position
            manager_runtime = restored_manager
            state_runtime = SimpleNamespace(
                _trade_id=None
            )

            execution_count = {
                "recovery": 0,
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
                execution_count["recovery"] += 1
                return real_recovery(
                    position=position,
                    manager=manager,
                    symbol=symbol,
                )

            runtime_globals = {
                "position_loaded": True,
                "position": position_runtime,
                "manager": manager_runtime,
                "SYMBOL": "BTCUSDT",
                "state": state_runtime,
                "recover_active_trade_from_durable_lifecycle": (
                    recovery_spy
                ),
                "print": print,
            }

            compiled = compile(
                ast.Module(
                    body=[startup_node],
                    type_ignores=[],
                ),
                "main.py",
                "exec",
            )

            exec(
                compiled,
                runtime_globals,
            )

            assert execution_count["recovery"] == 1

            assert (
                position_runtime.stop_loss
                == 101.0
            )

            assert (
                manager_runtime.snapshot()["tp1_hit"]
                is True
            )

            assert (
                manager_runtime.snapshot()["break_even"]
                is True
            )

            assert (
                manager_runtime.snapshot()["trailing"]
                is False
            )

            assert (
                state_runtime._trade_id
                == trade_uuid
            )

            assert (
                runtime_globals["plan"]["TradeUUID"]
                == trade_uuid
            )

            assert (
                runtime_globals["plan"]["Entry"]
                == 101.0
            )

            assert (
                runtime_globals["plan"]["Direction"]
                == "BUY"
            )

            print(
                "R56_POS24_ACTUAL_MAIN_STARTUP_BRANCH_EXECUTED: PASS"
            )

            print(
                "R56_POS24_MAIN_STARTUP_OVERRIDES_STALE_CACHE: PASS"
            )

            print(
                "R56_POS24_MAIN_STARTUP_RECOVERED_TP1_STATE: PASS"
            )

            print(
                "R56_POS24_MAIN_STARTUP_RESTORED_TRADE_ID: PASS"
            )

        finally:
            sm.FILE = original_file
            db.DB_PATH = original_db


if __name__ == "__main__":
    main()
