from pathlib import Path
import tempfile

import research.database as db
from engine.active_trade_recovery import persist_active_trade_lifecycle
from engine.position_manager import PositionManager
from engine.trade_manager import TradeManager


ENTRY = 100.0
SYMBOL = "BTCUSDT"


def run_case(name, previous, current):
    fd, path = tempfile.mkstemp(
        prefix="r56_pos26_flags_",
        suffix=".db",
    )
    Path(path).unlink()

    original_db = db.DB_PATH
    db.DB_PATH = path

    trade_uuid = f"TRADE-FLAG-{name}"
    auth = f"AUTH-FLAG-{name}"

    try:
        db.init_db()

        original_stop = 95.0
        tp1 = 105.0

        conn = db.get_connection()
        try:
            conn.execute(
                """
                INSERT INTO execution_intents (
                    authorization_id,
                    trade_uuid,
                    client_order_id,
                    broker_order_id,
                    symbol,
                    timeframe,
                    mode,
                    decision,
                    quantity,
                    requested_price,
                    stop_loss,
                    take_profit,
                    run_id,
                    status,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    auth,
                    trade_uuid,
                    f"CLIENT-{trade_uuid}",
                    f"BROKER-{trade_uuid}",
                    SYMBOL,
                    "15m",
                    "PAPER",
                    "LONG",
                    2.0,
                    ENTRY,
                    original_stop,
                    tp1,
                    "run-r56-pos26-flags",
                    "RECONCILED",
                    "2026-09-29T10:00:00",
                    "2026-09-29T10:00:00",
                ),
            )
            conn.commit()
        finally:
            conn.close()

        db.insert_active_trade_lifecycle(
            {
                "trade_uuid": trade_uuid,
                "authorization_id": auth,
                "symbol": SYMBOL,
                "position": "LONG",
                "current_stop": previous["current_stop"],
                "tp1_hit": previous["tp1_hit"],
                "tp2_hit": previous["tp2_hit"],
                "break_even": previous["break_even"],
                "trailing": previous["trailing"],
                "trade_closed": False,
                "revision": 2,
                "created_at": "2026-09-29T10:00:00",
                "updated_at": "2026-09-29T10:01:00",
            }
        )

        position = PositionManager()
        position.open_trade(
            "LONG",
            ENTRY,
            original_stop,
            tp1,
            position_size=2.0,
            initial_risk=10.0,
        )
        position.set_trade_uuid(trade_uuid)
        position.update_stop_loss(current["current_stop"])

        manager = TradeManager()
        manager.activate()
        manager.tp1_hit = current["tp1_hit"]
        manager.tp2_hit = current["tp2_hit"]
        manager.break_even = current["break_even"]
        manager.trailing = current["trailing"]

        plan = {
            "Direction": "BUY",
            "Entry": ENTRY,
            "StopLoss": original_stop,
            "TP1": 105.0,
            "TP2": 110.0,
            "TP3": 115.0,
        }

        try:
            revision = persist_active_trade_lifecycle(
                trade_uuid=trade_uuid,
                position=position,
                manager=manager,
                plan=plan,
                symbol=SYMBOL,
            )
        except Exception as exc:
            row = db.get_active_trade_lifecycle(trade_uuid)

            if row["revision"] != 2:
                raise AssertionError(
                    f"{name}: rejected lifecycle regression changed "
                    f"revision to {row['revision']}"
                )

            checks = {
                "tp1_hit": previous["tp1_hit"],
                "tp2_hit": previous["tp2_hit"],
                "break_even": previous["break_even"],
                "trailing": previous["trailing"],
                "current_stop": previous["current_stop"],
            }

            for field, expected in checks.items():
                actual = (
                    float(row[field])
                    if field == "current_stop"
                    else bool(row[field])
                )

                if actual != expected:
                    raise AssertionError(
                        f"{name}: rejected lifecycle regression "
                        f"mutated durable {field}: "
                        f"{actual!r} != {expected!r}"
                    )

            print(
                f"R56_POS26_{name}_FAIL_CLOSED: PASS "
                f"(revision={row['revision']}; durable state unchanged; "
                f"{exc})"
            )
            return

        row = db.get_active_trade_lifecycle(trade_uuid)

        print(
            f"R56_POS26_{name}_REGRESSION_GAP: CONFIRMED "
            f"(revision={revision}, durable_revision={row['revision']})"
        )

    finally:
        db.DB_PATH = original_db
        try:
            Path(path).unlink()
        except FileNotFoundError:
            pass


# Each new state is otherwise structurally valid and its stop satisfies
# the corresponding lifecycle phase. Only the lifecycle transition regresses.

run_case(
    "TP1",
    previous={
        "current_stop": 100.0,
        "tp1_hit": True,
        "tp2_hit": False,
        "break_even": True,
        "trailing": False,
    },
    current={
        "current_stop": 95.0,
        "tp1_hit": False,
        "tp2_hit": False,
        "break_even": False,
        "trailing": False,
    },
)

run_case(
    "TP2",
    previous={
        "current_stop": 108.0,
        "tp1_hit": True,
        "tp2_hit": True,
        "break_even": True,
        "trailing": True,
    },
    current={
        "current_stop": 100.0,
        "tp1_hit": True,
        "tp2_hit": False,
        "break_even": True,
        "trailing": False,
    },
)

run_case(
    "BREAK_EVEN",
    previous={
        "current_stop": 100.0,
        "tp1_hit": True,
        "tp2_hit": False,
        "break_even": True,
        "trailing": False,
    },
    current={
        "current_stop": 100.0,
        "tp1_hit": True,
        "tp2_hit": False,
        "break_even": False,
        "trailing": False,
    },
)

run_case(
    "TRAILING",
    previous={
        "current_stop": 108.0,
        "tp1_hit": True,
        "tp2_hit": True,
        "break_even": True,
        "trailing": True,
    },
    current={
        "current_stop": 108.0,
        "tp1_hit": True,
        "tp2_hit": True,
        "break_even": True,
        "trailing": False,
    },
)
