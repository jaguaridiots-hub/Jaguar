from pathlib import Path
import tempfile

import research.database as db
from engine.active_trade_recovery import persist_active_trade_lifecycle
from engine.position_manager import PositionManager
from engine.trade_manager import TradeManager


ENTRY = 100.0
SYMBOL = "BTCUSDT"


def run(direction, prior_stop, new_stop):
    fd, path = tempfile.mkstemp(
        prefix="r56_pos26_trail_",
        suffix=".db",
    )
    Path(path).unlink()

    original_db = db.DB_PATH
    db.DB_PATH = path

    trade_uuid = f"TRADE-TRAIL-{direction}"
    auth = f"AUTH-TRAIL-{direction}"

    try:
        db.init_db()

        original_stop = 95.0 if direction == "LONG" else 105.0
        tp1 = 105.0 if direction == "LONG" else 95.0

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
                    tp1,
                    "run-r56-pos26-trail",
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
                "position": direction,
                "current_stop": prior_stop,
                "tp1_hit": True,
                "tp2_hit": True,
                "break_even": True,
                "trailing": True,
                "trade_closed": False,
                "revision": 2,
                "created_at": "2026-09-29T10:00:00",
                "updated_at": "2026-09-29T10:01:00",
            }
        )

        position = PositionManager()
        position.open_trade(
            direction,
            ENTRY,
            original_stop,
            tp1,
            position_size=2.0,
            initial_risk=10.0,
        )
        position.set_trade_uuid(trade_uuid)
        position.update_stop_loss(new_stop)

        manager = TradeManager()
        manager.activate()
        manager.tp1_hit = True
        manager.tp2_hit = True
        manager.break_even = True
        manager.trailing = True

        plan = {
            "Direction": "BUY" if direction == "LONG" else "SELL",
            "Entry": ENTRY,
            "StopLoss": original_stop,
            "TP1": 105.0 if direction == "LONG" else 95.0,
            "TP2": 110.0 if direction == "LONG" else 90.0,
            "TP3": 115.0 if direction == "LONG" else 85.0,
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
                    f"{direction}: rejected trailing regression changed "
                    f"revision to {row['revision']}"
                )

            durable_stop = float(row["current_stop"])
            if abs(durable_stop - prior_stop) > 1e-8:
                raise AssertionError(
                    f"{direction}: rejected trailing regression changed "
                    f"durable stop to {durable_stop}"
                )

            print(
                f"R56_POS26_{direction}_TRAIL_NONREGRESSION_FAIL_CLOSED: "
                f"PASS (revision={row['revision']}; "
                f"durable stop unchanged; {exc})"
            )
            return

        row = db.get_active_trade_lifecycle(trade_uuid)

        print(
            f"R56_POS26_{direction}_TRAIL_REGRESSION_GAP: CONFIRMED "
            f"(prior_stop={prior_stop}, new_stop={new_stop}, "
            f"revision={revision}, durable_stop={row['current_stop']})"
        )

    finally:
        db.DB_PATH = original_db
        try:
            Path(path).unlink()
        except FileNotFoundError:
            pass


# Both new stops remain on the safe side of Entry, but move
# backward relative to the previous durable trailing stop.
run("LONG", 108.0, 105.0)
run("SHORT", 92.0, 95.0)
