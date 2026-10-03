from pathlib import Path
import tempfile

import research.database as db
from engine.active_trade_recovery import persist_active_trade_lifecycle
from engine.position_manager import PositionManager
from engine.trade_manager import TradeManager


ENTRY = 100.0
SYMBOL = "BTCUSDT"


def seed(*, trade_uuid, auth, direction):
    original_stop = 95.0 if direction == "LONG" else 105.0

    db.init_db()

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
                direction,
                2.0,
                ENTRY,
                original_stop,
                105.0 if direction == "LONG" else 95.0,
                "run-r56-pos26",
                "RECONCILED",
                "2026-09-29T10:00:00",
                "2026-09-29T10:00:00",
            ),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    db.insert_active_trade_lifecycle(
        {
            "trade_uuid": trade_uuid,
            "authorization_id": auth,
            "symbol": SYMBOL,
            "position": direction,
            "current_stop": original_stop,
            "tp1_hit": False,
            "tp2_hit": False,
            "break_even": False,
            "trailing": False,
            "trade_closed": False,
            "revision": 1,
            "created_at": "2026-09-29T10:00:00",
            "updated_at": "2026-09-29T10:00:00",
        }
    )


def make_plan(direction):
    return {
        "Direction": "BUY" if direction == "LONG" else "SELL",
        "Entry": ENTRY,
        "StopLoss": 95.0 if direction == "LONG" else 105.0,
        "TP1": 105.0 if direction == "LONG" else 95.0,
        "TP2": 110.0 if direction == "LONG" else 90.0,
        "TP3": 115.0 if direction == "LONG" else 85.0,
    }


def run_case(
    name,
    *,
    direction,
    current_stop,
    tp1_hit,
    tp2_hit,
    break_even,
    trailing,
    should_fail,
    expected_revision=1,
):
    fd, path = tempfile.mkstemp(
        prefix="r56_pos26_",
        suffix=".db",
    )
    Path(path).unlink()

    original_db = db.DB_PATH
    db.DB_PATH = path

    trade_uuid = f"TRADE-{name}"
    auth = f"AUTH-{name}"

    try:
        seed(
            trade_uuid=trade_uuid,
            auth=auth,
            direction=direction,
        )

        position = PositionManager()
        position.open_trade(
            direction,
            ENTRY,
            95.0 if direction == "LONG" else 105.0,
            105.0 if direction == "LONG" else 95.0,
            position_size=2.0,
            initial_risk=10.0,
        )
        position.set_trade_uuid(trade_uuid)
        position.update_stop_loss(current_stop)

        manager = TradeManager()
        manager.activate()
        manager.tp1_hit = tp1_hit
        manager.tp2_hit = tp2_hit
        manager.break_even = break_even
        manager.trailing = trailing

        plan = make_plan(direction)

        try:
            revision = persist_active_trade_lifecycle(
                trade_uuid=trade_uuid,
                position=position,
                manager=manager,
                plan=plan,
                symbol=SYMBOL,
            )
        except Exception as exc:
            if not should_fail:
                raise

            row = db.get_active_trade_lifecycle(trade_uuid)

            if row["revision"] != 1:
                raise AssertionError(
                    f"{name}: rejected write changed revision"
                )

            print(
                f"R56_POS26_{name}: PASS "
                f"({exc})"
            )
            return

        if should_fail:
            raise AssertionError(
                f"{name}: invalid stop was accepted"
            )

        row = db.get_active_trade_lifecycle(trade_uuid)

        if revision != expected_revision:
            raise AssertionError(
                f"{name}: expected revision "
                f"{expected_revision}, got {revision}"
            )

        if row["revision"] != expected_revision:
            raise AssertionError(
                f"{name}: durable revision is {row['revision']}"
            )

        if abs(float(row["current_stop"]) - current_stop) > 1e-8:
            raise AssertionError(
                f"{name}: durable stop mismatch"
            )

        print(f"R56_POS26_{name}: PASS")

    finally:
        db.DB_PATH = original_db
        try:
            Path(path).unlink()
        except FileNotFoundError:
            pass


# ------------------------------------------------------------
# Valid states
# ------------------------------------------------------------

run_case(
    "LONG_PRE_TP1_VALID",
    direction="LONG",
    current_stop=95.0,
    tp1_hit=False,
    tp2_hit=False,
    break_even=False,
    trailing=False,
    should_fail=False,
    expected_revision=1,
)

run_case(
    "SHORT_PRE_TP1_VALID",
    direction="SHORT",
    current_stop=105.0,
    tp1_hit=False,
    tp2_hit=False,
    break_even=False,
    trailing=False,
    should_fail=False,
    expected_revision=1,
)

run_case(
    "LONG_TP1_VALID",
    direction="LONG",
    current_stop=100.0,
    tp1_hit=True,
    tp2_hit=False,
    break_even=True,
    trailing=False,
    should_fail=False,
    expected_revision=2,
)

run_case(
    "SHORT_TP1_VALID",
    direction="SHORT",
    current_stop=100.0,
    tp1_hit=True,
    tp2_hit=False,
    break_even=True,
    trailing=False,
    should_fail=False,
    expected_revision=2,
)

run_case(
    "LONG_TP2_VALID",
    direction="LONG",
    current_stop=108.0,
    tp1_hit=True,
    tp2_hit=True,
    break_even=True,
    trailing=True,
    should_fail=False,
    expected_revision=2,
)

run_case(
    "SHORT_TP2_VALID",
    direction="SHORT",
    current_stop=92.0,
    tp1_hit=True,
    tp2_hit=True,
    break_even=True,
    trailing=True,
    should_fail=False,
    expected_revision=2,
)

# ------------------------------------------------------------
# Invalid states — must fail closed before DB revision advance
# ------------------------------------------------------------

run_case(
    "LONG_PRE_TP1_INVALID",
    direction="LONG",
    current_stop=94.0,
    tp1_hit=False,
    tp2_hit=False,
    break_even=False,
    trailing=False,
    should_fail=True,
)

run_case(
    "SHORT_PRE_TP1_INVALID",
    direction="SHORT",
    current_stop=106.0,
    tp1_hit=False,
    tp2_hit=False,
    break_even=False,
    trailing=False,
    should_fail=True,
)

run_case(
    "LONG_TP1_INVALID",
    direction="LONG",
    current_stop=101.0,
    tp1_hit=True,
    tp2_hit=False,
    break_even=True,
    trailing=False,
    should_fail=True,
)

run_case(
    "SHORT_TP1_INVALID",
    direction="SHORT",
    current_stop=99.0,
    tp1_hit=True,
    tp2_hit=False,
    break_even=True,
    trailing=False,
    should_fail=True,
)

run_case(
    "LONG_TP2_REGRESSION",
    direction="LONG",
    current_stop=99.0,
    tp1_hit=True,
    tp2_hit=True,
    break_even=True,
    trailing=True,
    should_fail=True,
)

run_case(
    "SHORT_TP2_REGRESSION",
    direction="SHORT",
    current_stop=101.0,
    tp1_hit=True,
    tp2_hit=True,
    break_even=True,
    trailing=True,
    should_fail=True,
)

print("R56-POS-26_WRITE_INVARIANT_WITNESS: PASS")
