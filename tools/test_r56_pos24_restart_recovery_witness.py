"""R56-POS-24 definitive DB-authoritative restart recovery witness."""

from pathlib import Path
from types import SimpleNamespace
import json
import tempfile

import intelligence.paper_post_fill as pp
import research.database as db

from engine.active_trade_recovery import (
    ActiveTradeRecoveryError,
    recover_active_trade_from_durable_lifecycle,
)
from engine.position_manager import PositionManager
from engine.trade_manager import TradeManager
from research.recorder import record_trade_open


def make_state(
    *,
    auth,
    trade_uuid,
    direction,
    fill_price,
):
    is_long = direction == "LONG"

    planned_entry = 100.0
    stop = 95.0 if is_long else 105.0
    targets = (
        [105.0, 110.0, 115.0]
        if is_long
        else [95.0, 90.0, 85.0]
    )

    execution_decision = (
        "ENTER_LONG"
        if is_long
        else "ENTER_SHORT"
    )

    enterprise_execution = {
        "authorization_id": auth,
        "client_order_id": (
            f"CLIENT-R56-POS24-{'LONG' if is_long else 'SHORT'}"
        ),
        "trade_uuid": trade_uuid,
        "symbol": "BTCUSDT",
        "decision": execution_decision,
        "entry": planned_entry,
        "stop_loss": stop,
        "targets": targets,
        "position_size": 2.0,
        "risk_amount": abs(planned_entry - stop) * 2.0,
        "mode": "PAPER",

        # Actual post-fill mutation persisted by the recorder.
        "fill_price": fill_price,
        "filled_quantity": 2.0,
        "order_status": "FILLED",
    }

    enterprise_trade = {
        "entry": planned_entry,
        "stop_loss": stop,
        "targets": targets,
    }

    return SimpleNamespace(
        symbol="BTCUSDT",
        interval="15m",
        mode="PAPER",
        price=fill_price,
        high=fill_price + 1.0,
        low=fill_price - 1.0,
        volume=1000.0,
        run_id="R56-POS24-RESTART-WITNESS",
        execution=enterprise_execution,
        trade=enterprise_trade,
        trade_plan={},
        idm={
            "decision": direction,
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


def insert_intent(
    *,
    auth,
    trade_uuid,
    direction,
    stop,
    tp1,
):
    is_long = direction == "LONG"

    db.insert_execution_intent(
        {
            "authorization_id": auth,
            "trade_uuid": trade_uuid,
            "client_order_id": (
                f"CLIENT-R56-POS24-{'LONG' if is_long else 'SHORT'}"
            ),
            "broker_order_id": None,
            "symbol": "BTCUSDT",
            "timeframe": "15m",
            "mode": "PAPER",
            "decision": direction,
            "quantity": 2.0,
            "requested_price": 100.0,
            "stop_loss": stop,
            "take_profit": tp1,
            "run_id": "R56-POS24-RESTART-WITNESS",
            "status": "AUTHORIZED",
            "created_at": "2026-09-29T00:00:00",
            "updated_at": "2026-09-29T00:00:00",
        }
    )

    db.update_execution_intent(
        auth,
        broker_order_id=(
            f"PAPER-R56-POS24-"
            f"{'LONG' if is_long else 'SHORT'}-001"
        ),
        status="SUBMITTED",
    )


def durable_paper_result(
    *,
    auth,
    direction,
    fill_price,
):
    is_long = direction == "LONG"

    return {
        "requested_quantity": 2.0,
        "filled_quantity": 2.0,
        "fill_price": fill_price,
        "remaining_quantity": 0.0,
        "order_status": "FILLED",
        "order": {
            "authorization_id": auth,
            "client_order_id": (
                f"CLIENT-R56-POS24-{'LONG' if is_long else 'SHORT'}"
            ),
            "broker_order_id": (
                f"PAPER-R56-POS24-"
                f"{'LONG' if is_long else 'SHORT'}-001"
            ),
            "symbol": "BTCUSDT",
            "side": "BUY" if is_long else "SELL",
            "requested_qty": 2.0,
            "filled_qty": 2.0,
            "remaining_qty": 0.0,
            "average_fill_price": fill_price,
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
            "stop_loss": 95.0 if is_long else 105.0,
            "targets": (
                [105.0, 110.0, 115.0]
                if is_long
                else [95.0, 90.0, 85.0]
            ),
        },
        "protection_reconciliation": {
            "reconciled": True,
        },
    }


def create_durable_trade(
    *,
    auth,
    trade_uuid,
    direction,
    fill_price,
):
    is_long = direction == "LONG"

    stop = 95.0 if is_long else 105.0
    tp1 = 105.0 if is_long else 95.0

    state = make_state(
        auth=auth,
        trade_uuid=trade_uuid,
        direction=direction,
        fill_price=fill_price,
    )

    insert_intent(
        auth=auth,
        trade_uuid=trade_uuid,
        direction=direction,
        stop=stop,
        tp1=tp1,
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
        execution_result=durable_paper_result(
            auth=auth,
            direction=direction,
            fill_price=fill_price,
        ),
        authorization_id=auth,
        filled_quantity=2.0,
        authorized_stop=stop,
        authorized_targets=(
            [105.0, 110.0, 115.0]
            if is_long
            else [95.0, 90.0, 85.0]
        ),
    )

    pp._persist_initial_active_trade_lifecycle(
        trade_uuid=trade_uuid,
        authorization_id=auth,
        direction=(
            "BUY"
            if direction == "LONG"
            else "SELL"
        ),
        authorized_stop=stop,
        SYMBOL="BTCUSDT",
    )

    intent = dict(
        db.get_execution_intent(auth)
    )

    assert intent["status"] == "RECONCILED"

    lifecycle = dict(
        db.get_active_trade_lifecycle(trade_uuid)
    )

    assert lifecycle["revision"] == 1
    assert lifecycle["trade_closed"] == 0
    assert lifecycle["tp1_hit"] == 0
    assert lifecycle["tp2_hit"] == 0
    assert lifecycle["break_even"] == 0
    assert lifecycle["trailing"] == 0

    return state


def count_execution_intents():
    conn = db.get_connection()
    try:
        return int(
            conn.execute(
                "SELECT COUNT(*) AS n FROM execution_intents"
            ).fetchone()["n"]
        )
    finally:
        conn.close()


def recover_and_assert(
    *,
    direction,
    fill_price,
    expected_stop,
    expected_tp1,
):
    position = PositionManager()
    manager = TradeManager()

    before_intents = count_execution_intents()

    plan = recover_active_trade_from_durable_lifecycle(
        position=position,
        manager=manager,
        symbol="BTCUSDT",
    )

    after_intents = count_execution_intents()

    assert after_intents == before_intents

    assert plan["Direction"] == (
        "BUY" if direction == "LONG" else "SELL"
    )

    assert float(plan["Entry"]) == float(fill_price)
    assert float(position.entry) == float(fill_price)
    assert float(position.stop_loss) == float(expected_stop)
    assert float(position.take_profit) == float(expected_tp1)
    assert float(position.position_size) == 2.0

    expected_initial_risk = (
        abs(fill_price - expected_stop) * 2.0
    )

    assert abs(
        float(position.initial_risk)
        - expected_initial_risk
    ) < 1e-8

    assert position.trade_uuid == plan["TradeUUID"]

    snapshot = manager.snapshot()

    assert snapshot["position_open"] is True
    assert snapshot["trade_closed"] is False
    assert snapshot["tp1_hit"] is False
    assert snapshot["tp2_hit"] is False
    assert snapshot["break_even"] is False
    assert snapshot["trailing"] is False

    print(
        f"R56_POS24_{direction}_ACTUAL_FILL_RECOVERED: PASS"
    )
    print(
        f"R56_POS24_{direction}_INITIAL_RISK_RECOVERED: PASS"
    )
    print(
        f"R56_POS24_{direction}_MANAGER_RECONSTRUCTED: PASS"
    )
    print(
        f"R56_POS24_{direction}_NO_NEW_EXECUTION: PASS"
    )

    return plan


def update_to_tp1(
    *,
    trade_uuid,
):
    current = dict(
        db.get_active_trade_lifecycle(trade_uuid)
    )

    db.update_active_trade_lifecycle(
        trade_uuid,
        authorization_id=current["authorization_id"],
        symbol=current["symbol"],
        position=current["position"],
        current_stop=101.0
        if current["position"] == "LONG"
        else 99.0,
        tp1_hit=True,
        tp2_hit=False,
        break_even=True,
        trailing=False,
        revision=2,
        expected_revision=current["revision"],
        updated_at="2026-09-29T00:02:00",
    )


def assert_tp1_recovery(
    *,
    direction,
    trade_uuid,
    fill_price,
):
    position = PositionManager()
    manager = TradeManager()

    plan = recover_active_trade_from_durable_lifecycle(
        position=position,
        manager=manager,
        symbol="BTCUSDT",
    )

    expected_stop = (
        101.0
        if direction == "LONG"
        else 99.0
    )

    assert float(plan["Entry"]) == float(fill_price)
    assert float(position.entry) == float(fill_price)
    assert float(position.stop_loss) == expected_stop

    snapshot = manager.snapshot()

    assert snapshot["position_open"] is True
    assert snapshot["trade_closed"] is False
    assert snapshot["tp1_hit"] is True
    assert snapshot["tp2_hit"] is False
    assert snapshot["break_even"] is True
    assert snapshot["trailing"] is False

    lifecycle = dict(
        db.get_active_trade_lifecycle(trade_uuid)
    )

    assert lifecycle["revision"] == 2

    print(
        f"R56_POS24_{direction}_TP1_LIFECYCLE_RECOVERED: PASS"
    )


def assert_snapshot_checksum_failure(
    *,
    trade_uuid,
):
    conn = db.get_connection()

    try:
        row = conn.execute(
            """
            SELECT snapshot_open
            FROM trades
            WHERE uuid = ?
            """,
            (trade_uuid,),
        ).fetchone()

        assert row is not None

        snapshot = json.loads(
            row["snapshot_open"]
        )

        snapshot["enterprise_execution"][
            "fill_price"
        ] = 999.0

        conn.execute(
            """
            UPDATE trades
            SET snapshot_open = ?
            WHERE uuid = ?
            """,
            (
                json.dumps(
                    snapshot,
                    sort_keys=True,
                ),
                trade_uuid,
            ),
        )
        conn.commit()
    finally:
        conn.close()

    try:
        recover_active_trade_from_durable_lifecycle(
            position=PositionManager(),
            manager=TradeManager(),
            symbol="BTCUSDT",
        )
    except ActiveTradeRecoveryError as exc:
        assert "checksum mismatch" in str(exc).lower()

        print(
            "R56_POS24_SNAPSHOT_CHECKSUM_FAIL_CLOSED: PASS"
        )
    else:
        raise AssertionError(
            "Tampered durable snapshot was accepted"
        )


def assert_lifecycle_checksum_failure(
    *,
    trade_uuid,
):
    lifecycle = dict(
        db.get_active_trade_lifecycle(trade_uuid)
    )

    conn = db.get_connection()

    try:
        conn.execute(
            """
            UPDATE active_trade_lifecycle
            SET current_stop = ?
            WHERE trade_uuid = ?
            """,
            (
                float(lifecycle["current_stop"]) + 1.0,
                trade_uuid,
            ),
        )
        conn.commit()
    finally:
        conn.close()

    try:
        recover_active_trade_from_durable_lifecycle(
            position=PositionManager(),
            manager=TradeManager(),
            symbol="BTCUSDT",
        )
    except RuntimeError as exc:
        assert "checksum mismatch" in str(exc).lower()

        print(
            "R56_POS24_LIFECYCLE_CHECKSUM_FAIL_CLOSED: PASS"
        )
    else:
        raise AssertionError(
            "Corrupted durable lifecycle was accepted"
        )


def main():
    with tempfile.TemporaryDirectory(
        dir=".jaguar_audit",
        prefix="r56-pos24-restart-",
    ) as td:
        temp_db = Path(td) / "restart-recovery.db"

        original_db = db.DB_PATH
        db.DB_PATH = str(temp_db)

        try:
            db.init_db()

            # LONG: planned entry 100, actual fill 101.
            long_auth = "AUTH-R56-POS24-REC-LONG"
            long_trade = "TRADE-R56-POS24-REC-LONG"

            create_durable_trade(
                auth=long_auth,
                trade_uuid=long_trade,
                direction="LONG",
                fill_price=101.0,
            )

            recover_and_assert(
                direction="LONG",
                fill_price=101.0,
                expected_stop=95.0,
                expected_tp1=105.0,
            )

            update_to_tp1(
                trade_uuid=long_trade,
            )

            assert_tp1_recovery(
                direction="LONG",
                trade_uuid=long_trade,
                fill_price=101.0,
            )

            # Only the lifecycle corruption witness should run on a
            # dedicated database state because corruption is deliberate.
            assert_lifecycle_checksum_failure(
                trade_uuid=long_trade,
            )

            # Snapshot checksum witness uses a fresh isolated database.
            second_db = Path(td) / "snapshot-checksum.db"

            db.DB_PATH = str(second_db)
            db.init_db()

            short_auth = "AUTH-R56-POS24-REC-SHORT"
            short_trade = "TRADE-R56-POS24-REC-SHORT"

            create_durable_trade(
                auth=short_auth,
                trade_uuid=short_trade,
                direction="SHORT",
                fill_price=99.0,
            )

            recover_and_assert(
                direction="SHORT",
                fill_price=99.0,
                expected_stop=105.0,
                expected_tp1=95.0,
            )

            assert_snapshot_checksum_failure(
                trade_uuid=short_trade,
            )

            # Missing lifecycle is intentionally a discovery miss.
            # The startup caller will retain the POS-23 orphan barrier.
            lifecycle = dict(
                db.get_active_trade_lifecycle(short_trade)
            )

            db.delete_active_trade_lifecycle(
                short_trade
            )

            position = PositionManager()
            manager = TradeManager()

            result = recover_active_trade_from_durable_lifecycle(
                position=position,
                manager=manager,
                symbol="BTCUSDT",
            )

            assert result is None
            assert position.position == "NONE"
            assert manager.snapshot()["position_open"] is False

            print(
                "R56_POS24_MISSING_LIFECYCLE_RETURNS_NONE: PASS"
            )

        finally:
            db.DB_PATH = original_db


if __name__ == "__main__":
    main()
