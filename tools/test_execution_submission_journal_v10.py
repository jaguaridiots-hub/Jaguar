import os
import tempfile
from importlib import reload

from research import database as db


tmpdir = tempfile.TemporaryDirectory()
os.environ["JAGUAR_DB_PATH"] = os.path.join(
    tmpdir.name,
    "journal.sqlite",
)

reload(db)

conn = db.init_db()
conn.close()

conn = db.get_connection()
try:
    version = db._get_schema_version(conn.cursor())
finally:
    conn.close()

assert version == 10, version

db.insert_execution_intent({
    "authorization_id": "AUTH-001",
    "trade_uuid": "TRADE-001",
    "client_order_id": "JQX-001",
    "symbol": "NSE_EQ|TEST",
    "timeframe": "15m",
    "mode": "LIVE",
    "decision": "LONG",
    "quantity": 10,
    "status": "AUTHORIZED",
    "created_at": "2026-09-09T00:00:00",
    "updated_at": "2026-09-09T00:00:00",
})

db.insert_execution_submission({
    "submission_id": "SUB-001",
    "authorization_id": "AUTH-001",
    "trade_uuid": "TRADE-001",
    "client_order_id": "JQX-001",
    "symbol": "NSE_EQ|TEST",
    "instrument_token": "NSE_EQ|TEST",
    "transaction_type": "BUY",
    "requested_qty": 10,
    "status": "SUBMITTING",
    "created_at": "2026-09-09T00:00:00",
    "updated_at": "2026-09-09T00:00:00",
})

row = db.get_execution_submission("SUB-001")
assert row is not None
assert row["status"] == "SUBMITTING"
assert row["broker_order_id"] is None

tag_row = db.get_execution_submission_by_client_order_id("JQX-001")
assert tag_row["submission_id"] == "SUB-001"

db.update_execution_submission(
    "SUB-001",
    status="IDENTIFIED",
    broker_order_id="UP-001",
)

row = db.get_execution_submission("SUB-001")
assert row["status"] == "IDENTIFIED"
assert row["broker_order_id"] == "UP-001"

db.update_execution_submission(
    "SUB-001",
    status="LINEAGE_PERSISTED",
)

row = db.get_execution_submission("SUB-001")
assert row["status"] == "LINEAGE_PERSISTED"

try:
    db.update_execution_submission(
        "SUB-001",
        status="HALTED",
    )
except RuntimeError:
    pass
else:
    raise AssertionError(
        "Terminal submission journal was mutable"
    )

try:
    db.update_execution_submission(
        "SUB-001",
        broker_order_id="UP-002",
    )
except RuntimeError:
    pass
else:
    raise AssertionError(
        "Terminal broker identity was mutable"
    )

print("V10_SUBMISSION_JOURNAL_SCHEMA: PASS")
print("V10_SUBMISSION_JOURNAL_PERSISTENCE: PASS")
print("V10_SUBMISSION_JOURNAL_IDENTITY_LOOKUP: PASS")
print("V10_SUBMISSION_JOURNAL_ID_IMMUTABILITY: PASS")
print("V10_SUBMISSION_JOURNAL_TERMINAL_IMMUTABILITY: PASS")


# Verify legacy schema-drift repair cannot regress V10 to version 8.
drift_tmp = tempfile.TemporaryDirectory()
os.environ["JAGUAR_DB_PATH"] = os.path.join(
    drift_tmp.name,
    "drift.sqlite",
)

reload(db)

conn = db.init_db()
try:
    conn.execute(
        "ALTER TABLE trades RENAME COLUMN asset_class TO asset_class_backup"
    )
    conn.commit()
finally:
    conn.close()

conn = db.init_db()

try:
    repaired_version = db._get_schema_version(conn.cursor())
    journal = conn.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
          AND name = 'execution_submission_journal'
        """
    ).fetchone()
finally:
    conn.close()

assert repaired_version == 10, repaired_version
assert journal is not None

print("V10_SCHEMA_DRIFT_VERSION_PRESERVED: PASS")
print("V10_SCHEMA_DRIFT_JOURNAL_PRESERVED: PASS")
