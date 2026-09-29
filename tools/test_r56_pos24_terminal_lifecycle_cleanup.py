"""R56-POS-24C terminal active-lifecycle cleanup witness."""

from pathlib import Path
import sqlite3
import tempfile

import research.database as db


MAIN = Path("main.py").read_text()


def source_order_assertions():
    close_call = MAIN.index(
        "record_trade_close("
    )

    status_check = MAIN.index(
        'if closed_row["status"] != "CLOSED":'
    )

    timestamp_check = MAIN.index(
        'if closed_row["close_time"] is None:'
    )

    exit_check = MAIN.index(
        'if float(closed_row["exit_price"]) != exit_price:'
    )

    pnl_check = MAIN.index(
        'if float(closed_row["pnl"]) != pnl:'
    )

    delete_call = MAIN.index(
        "delete_active_trade_lifecycle("
    )

    local_clear = MAIN.index(
        "state._trade_id = None",
        delete_call,
    )

    position_close = MAIN.index(
        "position.close_trade()",
        delete_call,
    )

    manager_deactivate = MAIN.index(
        "manager.deactivate()",
        delete_call,
    )

    state_clear = MAIN.index(
        "clear()",
        delete_call,
    )

    assert close_call < status_check
    assert status_check < timestamp_check
    assert timestamp_check < exit_check
    assert exit_check < pnl_check
    assert pnl_check < delete_call
    assert delete_call < local_clear
    assert delete_call < position_close
    assert delete_call < manager_deactivate
    assert delete_call < state_clear

    print(
        "R56_POS24_TERMINAL_CLOSE_BEFORE_LIFECYCLE_DELETE: PASS"
    )

    print(
        "R56_POS24_LIFECYCLE_DELETE_BEFORE_LOCAL_CLEAR: PASS"
    )


def database_cleanup_witness():
    with tempfile.TemporaryDirectory(
        dir=".jaguar_audit",
        prefix="r56-pos24-close-",
    ) as td:

        temp_db = Path(td) / "terminal-cleanup.db"

        original_db = db.DB_PATH
        db.DB_PATH = str(temp_db)

        try:
            db.init_db()

            auth = "AUTH-R56-POS24-CLOSE"
            trade = "TRADE-R56-POS24-CLOSE"

            db.insert_execution_intent(
                {
                    "authorization_id": auth,
                    "trade_uuid": trade,
                    "client_order_id": "CLIENT-R56-POS24-CLOSE",
                    "broker_order_id": "PAPER-R56-POS24-CLOSE",
                    "symbol": "BTCUSDT",
                    "timeframe": "15m",
                    "mode": "PAPER",
                    "decision": "LONG",
                    "quantity": 2.0,
                    "requested_price": 100.0,
                    "stop_loss": 95.0,
                    "take_profit": 105.0,
                    "run_id": "R56-POS24-CLOSE",
                    "status": "AUTHORIZED",
                    "created_at": "2026-09-29T00:00:00",
                    "updated_at": "2026-09-29T00:00:00",
                }
            )

            db.update_execution_intent(
                auth,
                broker_order_id="PAPER-R56-POS24-CLOSE",
                status="SUBMITTED",
            )

            conn = db.get_connection()
            try:
                conn.execute(
                    """
                    INSERT INTO trades (
                        uuid,
                        authorization_id,
                        status,
                        open_time,
                        symbol,
                        timeframe,
                        mode,
                        entry_price,
                        stop_loss,
                        take_profit,
                        close_time,
                        exit_price,
                        pnl
                    )
                    VALUES (?, ?, 'OPEN', ?, ?, ?, ?, ?, ?, ?, NULL, NULL, NULL)
                    """,
                    (
                        trade,
                        auth,
                        "2026-09-29T00:00:00",
                        "BTCUSDT",
                        "15m",
                        "PAPER",
                        101.0,
                        95.0,
                        105.0,
                    ),
                )
                conn.commit()
            finally:
                conn.close()

            db.insert_active_trade_lifecycle(
                {
                    "trade_uuid": trade,
                    "authorization_id": auth,
                    "symbol": "BTCUSDT",
                    "position": "LONG",
                    "current_stop": 101.0,
                    "tp1_hit": True,
                    "tp2_hit": False,
                    "break_even": True,
                    "trailing": False,
                    "trade_closed": False,
                    "revision": 2,
                    "created_at": "2026-09-29T00:01:00",
                    "updated_at": "2026-09-29T00:02:00",
                }
            )

            # Simulate the already-verified canonical close boundary.
            conn = db.get_connection()
            try:
                conn.execute(
                    """
                    UPDATE trades
                    SET
                        status = 'CLOSED',
                        close_time = ?,
                        exit_price = ?,
                        pnl = ?
                    WHERE uuid = ?
                    """,
                    (
                        "2026-09-29T00:03:00",
                        110.0,
                        18.0,
                        trade,
                    ),
                )
                conn.commit()
            finally:
                conn.close()

            before = db.get_active_trade_lifecycle(
                trade
            )

            assert before is not None

            deleted = db.delete_active_trade_lifecycle(
                trade
            )

            assert deleted == 1

            after = db.get_active_trade_lifecycle(
                trade
            )

            assert after is None

            conn = db.get_connection()
            try:
                closed = conn.execute(
                    """
                    SELECT status, close_time
                    FROM trades
                    WHERE uuid = ?
                    """,
                    (trade,),
                ).fetchone()
            finally:
                conn.close()

            assert closed["status"] == "CLOSED"
            assert closed["close_time"] is not None

            print(
                "R56_POS24_CLOSED_TRADE_LIFECYCLE_REMOVED: PASS"
            )

            # A second deletion must not falsely report success.
            second_delete = db.delete_active_trade_lifecycle(
                trade
            )

            assert second_delete == 0

            print(
                "R56_POS24_REPEAT_DELETE_NOT_SUCCESSFUL: PASS"
            )

        finally:
            db.DB_PATH = original_db


def main():
    source_order_assertions()
    database_cleanup_witness()

    print(
        "R56-POS-24C_TERMINAL_LIFECYCLE_CLEANUP: PASS"
    )


if __name__ == "__main__":
    main()
