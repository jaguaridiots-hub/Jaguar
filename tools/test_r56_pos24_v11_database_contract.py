from pathlib import Path
import tempfile

import research.database as db


AUTH = "auth-pos24-v11"
TRADE = "trade-pos24-v11"
CLIENT = "client-pos24-v11"


def seed_execution_intent():
    conn = db.get_connection()
    try:
        conn.execute(
            """
            INSERT INTO execution_intents (
                authorization_id,
                trade_uuid,
                client_order_id,
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
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                AUTH,
                TRADE,
                CLIENT,
                "TEST",
                "1h",
                "PAPER",
                "ENTER_LONG",
                1.0,
                100.0,
                95.0,
                110.0,
                "run-pos24-v11",
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


def lifecycle(
    *,
    current_stop=95.0,
    tp1_hit=False,
    tp2_hit=False,
    break_even=False,
    trailing=False,
    revision=1,
):
    return {
        "trade_uuid": TRADE,
        "authorization_id": AUTH,
        "symbol": "TEST",
        "position": "LONG",
        "current_stop": current_stop,
        "tp1_hit": tp1_hit,
        "tp2_hit": tp2_hit,
        "break_even": break_even,
        "trailing": trailing,
        "trade_closed": False,
        "revision": revision,
        "created_at": "2026-09-29T10:00:00",
        "updated_at": "2026-09-29T10:00:00",
    }


with tempfile.TemporaryDirectory(prefix="jaguar-pos24-v11-") as td:
    db_path = Path(td) / "test.db"
    original = db.DB_PATH
    db.DB_PATH = str(db_path)

    try:
        # ------------------------------------------------------------
        # Schema + idempotent migration
        # ------------------------------------------------------------
        db.init_db()
        db.init_db()

        conn = db.get_connection()
        try:
            version = conn.execute(
                "SELECT value FROM meta WHERE key='schema_version'"
            ).fetchone()["value"]

            table = conn.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type='table'
                  AND name='active_trade_lifecycle'
                """
            ).fetchone()
        finally:
            conn.close()

        assert version == "11"
        assert table is not None
        print("R56_POS24_V11_IDEMPOTENT_MIGRATION: PASS")

        # ------------------------------------------------------------
        # Seed canonical execution identity
        # ------------------------------------------------------------
        seed_execution_intent()

        # ------------------------------------------------------------
        # Initial durable lifecycle
        # ------------------------------------------------------------
        db.insert_active_trade_lifecycle(
            lifecycle()
        )

        row = db.get_active_trade_lifecycle(TRADE)

        assert row is not None
        assert row["trade_uuid"] == TRADE
        assert row["authorization_id"] == AUTH
        assert row["symbol"] == "TEST"
        assert row["position"] == "LONG"
        assert float(row["current_stop"]) == 95.0
        assert row["revision"] == 1
        assert row["trade_closed"] == 0

        print("R56_POS24_V11_INITIAL_INSERT: PASS")

        # ------------------------------------------------------------
        # Valid CAS update
        # ------------------------------------------------------------
        db.update_active_trade_lifecycle(
            TRADE,
            authorization_id=AUTH,
            symbol="TEST",
            position="LONG",
            current_stop=100.0,
            tp1_hit=True,
            tp2_hit=False,
            break_even=True,
            trailing=False,
            revision=2,
            expected_revision=1,
            updated_at="2026-09-29T10:01:00",
        )

        row = db.get_active_trade_lifecycle(TRADE)

        assert float(row["current_stop"]) == 100.0
        assert row["tp1_hit"] == 1
        assert row["break_even"] == 1
        assert row["revision"] == 2

        print("R56_POS24_V11_CAS_UPDATE: PASS")

        # ------------------------------------------------------------
        # Stale revision must fail closed
        # ------------------------------------------------------------
        try:
            db.update_active_trade_lifecycle(
                TRADE,
                authorization_id=AUTH,
                symbol="TEST",
                position="LONG",
                current_stop=101.0,
                tp1_hit=True,
                tp2_hit=False,
                break_even=True,
                trailing=False,
                revision=3,
                expected_revision=1,
                updated_at="2026-09-29T10:02:00",
            )
        except Exception:
            print("R56_POS24_V11_STALE_REVISION_FAIL_CLOSED: PASS")
        else:
            raise RuntimeError(
                "FAIL: stale revision accepted"
            )

        # ------------------------------------------------------------
        # Identity mutation must fail closed
        # ------------------------------------------------------------
        try:
            db.update_active_trade_lifecycle(
                TRADE,
                authorization_id="WRONG-AUTH",
                symbol="TEST",
                position="LONG",
                current_stop=101.0,
                tp1_hit=True,
                tp2_hit=False,
                break_even=True,
                trailing=False,
                revision=3,
                expected_revision=2,
                updated_at="2026-09-29T10:02:00",
            )
        except Exception:
            print("R56_POS24_V11_IDENTITY_IMMUTABILITY: PASS")
        else:
            raise RuntimeError(
                "FAIL: authorization identity mutation accepted"
            )

        # ------------------------------------------------------------
        # Invalid lifecycle ordering
        # ------------------------------------------------------------
        try:
            db.update_active_trade_lifecycle(
                TRADE,
                authorization_id=AUTH,
                symbol="TEST",
                position="LONG",
                current_stop=101.0,
                tp1_hit=False,
                tp2_hit=True,
                break_even=False,
                trailing=True,
                revision=3,
                expected_revision=2,
                updated_at="2026-09-29T10:03:00",
            )
        except Exception:
            print("R56_POS24_V11_INVALID_ORDER_FAIL_CLOSED: PASS")
        else:
            raise RuntimeError(
                "FAIL: invalid TP/trailing ordering accepted"
            )

        # ------------------------------------------------------------
        # Terminal lifecycle must fail closed
        # ------------------------------------------------------------
        try:
            bad = lifecycle()
            bad["trade_closed"] = True
            db.insert_active_trade_lifecycle(bad)
        except Exception:
            print("R56_POS24_V11_TERMINAL_INSERT_FAIL_CLOSED: PASS")
        else:
            raise RuntimeError(
                "FAIL: terminal lifecycle accepted"
            )

        # ------------------------------------------------------------
        # Corrupt checksum directly.
        #
        # The read API MUST NOT silently return corrupted lifecycle
        # state. Either it rejects the row, or this test exposes the
        # missing fail-closed validation.
        # ------------------------------------------------------------
        conn = db.get_connection()
        try:
            conn.execute(
                """
                UPDATE active_trade_lifecycle
                SET state_checksum = ?
                WHERE trade_uuid = ?
                """,
                ("CORRUPTED", TRADE),
            )
            conn.commit()
        finally:
            conn.close()

        try:
            row = db.get_active_trade_lifecycle(TRADE)
        except Exception:
            print("R56_POS24_V11_CHECKSUM_CORRUPTION_FAIL_CLOSED: PASS")
        else:
            if row is not None and row["state_checksum"] == "CORRUPTED":
                raise RuntimeError(
                    "FAIL: corrupted checksum returned without validation"
                )

            raise RuntimeError(
                "FAIL: checksum corruption handling is not fail-closed"
            )

        # ------------------------------------------------------------
        # Delete
        # ------------------------------------------------------------
        deleted = db.delete_active_trade_lifecycle(TRADE)
        assert deleted == 1
        assert db.get_active_trade_lifecycle(TRADE) is None

        print("R56_POS24_V11_DELETE: PASS")

    finally:
        db.DB_PATH = original


print("R56-POS-24_V11_DATABASE_CONTRACT: PASS")
