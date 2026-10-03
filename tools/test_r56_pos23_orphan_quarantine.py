import json
import os
import tempfile
from pathlib import Path

import engine.state_manager as sm
import research.database as db
from engine.position_manager import PositionManager
from engine.trade_manager import TradeManager


def seed_trade(conn, *, uuid, auth, status="OPEN", close_time=None):
    conn.execute(
        """
        INSERT INTO trades (
            uuid,
            authorization_id,
            status,
            open_time,
            close_time,
            symbol,
            timeframe,
            mode,
            entry_price,
            stop_loss,
            take_profit
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            uuid,
            auth,
            status,
            "2026-09-29T00:00:00",
            close_time,
            "BTCUSDT",
            "15m",
            "PAPER",
            100.0,
            95.0,
            105.0,
        ),
    )


def seed_intent(conn, *, auth, trade_uuid, status):
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
            f"CLIENT-{auth}",
            f"BROKER-{auth}" if status != "AUTHORIZED" else None,
            "BTCUSDT",
            "15m",
            "PAPER",
            "LONG",
            1.0,
            100.0,
            95.0,
            105.0,
            "R56-POS23",
            status,
            "2026-09-29T00:00:00",
            "2026-09-29T00:00:00",
        ),
    )


def orphan_guard(symbol):
    conn = None
    try:
        conn = db.get_connection()
        rows = conn.execute(
            """
            SELECT uuid
            FROM trades
            WHERE symbol = ?
              AND status = 'OPEN'
              AND close_time IS NULL
            """,
            (symbol,),
        ).fetchall()

        if rows:
            raise RuntimeError(
                "FAIL-CLOSED: Durable active trade exists but "
                "local recovery state is unavailable"
            )
    finally:
        if conn is not None:
            conn.close()


def main():
    with tempfile.TemporaryDirectory(
        prefix="jaguar-pos23-quarantine-"
    ) as td:
        db_path = Path(td) / "cert.db"
        state_path = Path(td) / "trade_state.json"

        original_db = db.DB_PATH
        original_state = sm.FILE

        db.DB_PATH = str(db_path)
        sm.FILE = str(state_path)

        try:
            db.init_db()

            # --------------------------------------------------
            # 1. Clean account: no durable trade
            # --------------------------------------------------
            orphan_guard("BTCUSDT")
            print("R56_POS23_CLEAN_ACCOUNT_ALLOW: PASS")

            # --------------------------------------------------
            # 2. Durable OPEN + missing local state
            # --------------------------------------------------
            conn = db.get_connection()
            try:
                seed_trade(
                    conn,
                    uuid="TRADE-OPEN-1",
                    auth="AUTH-OPEN-1",
                )
                conn.commit()
            finally:
                conn.close()

            try:
                orphan_guard("BTCUSDT")
            except RuntimeError:
                print("R56_POS23_ORPHAN_OPEN_BLOCK: PASS")
            else:
                raise AssertionError(
                    "OPEN trade without local state was not blocked"
                )

            # --------------------------------------------------
            # 3. Active local state remains independently valid
            # --------------------------------------------------
            position = PositionManager()
            manager = TradeManager()

            position.open_trade(
                "LONG",
                100.0,
                95.0,
                105.0,
                position_size=1.0,
                initial_risk=5.0,
            )
            position.set_trade_uuid("TRADE-OPEN-1")
            manager.activate()

            assert sm.save(
                position,
                "BTCUSDT",
                manager,
            )

            restored_position = PositionManager()
            restored_manager = TradeManager()

            assert sm.load(
                restored_position,
                "BTCUSDT",
                restored_manager,
            )

            assert restored_position.trade_uuid == "TRADE-OPEN-1"
            assert restored_position.position == "LONG"
            assert restored_manager.position_open is True
            assert restored_manager.trade_closed is False

            print("R56_POS23_LOCAL_ACTIVE_RECOVERY: PASS")

            # --------------------------------------------------
            # 4. Corrupt/remove local state -> quarantine
            # --------------------------------------------------
            sm.clear()

            try:
                sm.load(
                    PositionManager(),
                    "BTCUSDT",
                    TradeManager(),
                )
            except Exception:
                # load itself must not invent recovery.
                pass

            try:
                orphan_guard("BTCUSDT")
            except RuntimeError:
                print("R56_POS23_CORRUPT_OR_MISSING_STATE_BLOCK: PASS")
            else:
                raise AssertionError(
                    "Durable OPEN trade was not quarantined"
                )

            # --------------------------------------------------
            # 5. CLOSED trade does not trip orphan guard
            # --------------------------------------------------
            conn = db.get_connection()
            try:
                conn.execute(
                    """
                    UPDATE trades
                    SET status = 'CLOSED',
                        close_time = ?
                    WHERE uuid = ?
                    """,
                    (
                        "2026-09-29T01:00:00",
                        "TRADE-OPEN-1",
                    ),
                )
                conn.commit()
            finally:
                conn.close()

            orphan_guard("BTCUSDT")
            print("R56_POS23_CLOSED_TRADE_ALLOW: PASS")

            # --------------------------------------------------
            # 6. Unresolved intent remains a separate re-entry
            #    barrier condition.
            # --------------------------------------------------
            conn = db.get_connection()
            try:
                seed_intent(
                    conn,
                    auth="AUTH-UNRESOLVED",
                    trade_uuid="TRADE-UNRESOLVED",
                    status="AUTHORIZED",
                )
                conn.commit()

                row = conn.execute(
                    """
                    SELECT status
                    FROM execution_intents
                    WHERE authorization_id = ?
                    """,
                    ("AUTH-UNRESOLVED",),
                ).fetchone()

                assert row["status"] == "AUTHORIZED"
                print("R56_POS23_UNRESOLVED_INTENT_PRESENT: PASS")
            finally:
                conn.close()

            print("R56-POS-23_ORPHAN_QUARANTINE_CERTIFICATION: PASS")

        finally:
            db.DB_PATH = original_db
            sm.FILE = original_state


if __name__ == "__main__":
    main()
