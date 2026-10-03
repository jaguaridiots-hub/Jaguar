import hashlib
import json
import sqlite3
import tempfile
from pathlib import Path

import research.analytics_advanced as aa
import research.research_report as rr
import research.trade_forensics as tf
from research.closed_trade_integrity import (
    validate_closed_trade_record,
)


def make_snapshot(
    *,
    exit_price=110.0,
    pnl=8.5,
    r_multiple=1.7,
    win_loss=True,
    holding_time=12,
    timestamp="2026-09-30T12:00:00",
):
    return {
        "exit_price": exit_price,
        "pnl": pnl,
        "r_multiple": r_multiple,
        "win_loss": win_loss,
        "holding_time": holding_time,
        "timestamp": timestamp,
    }


def make_closed_row(
    uuid,
    *,
    symbol="TEST",
    pnl=8.5,
    r_multiple=1.7,
):
    snapshot = make_snapshot(
        pnl=pnl,
        r_multiple=r_multiple,
        win_loss=(pnl > 0),
    )

    return (
        uuid,
        "CLOSED",
        snapshot["timestamp"],
        snapshot["exit_price"],
        snapshot["pnl"],
        snapshot["r_multiple"],
        1 if snapshot["win_loss"] else 0,
        snapshot["holding_time"],
        json.dumps(snapshot),
        hashlib.sha256(
            json.dumps(
                snapshot,
                sort_keys=True,
            ).encode()
        ).hexdigest(),
        "2026-09-30T11:00:00",
        symbol,
        "PAPER",
        "EQUITY",
    )


def make_db(path):
    conn = sqlite3.connect(path)

    conn.execute("""
        CREATE TABLE trades (
            uuid TEXT,
            status TEXT,
            close_time TEXT,
            exit_price REAL,
            pnl REAL,
            r_multiple REAL,
            win_loss INTEGER,
            holding_time INTEGER,
            snapshot_close TEXT,
            snapshot_close_checksum TEXT,
            open_time TEXT,
            symbol TEXT,
            mode TEXT,
            asset_class TEXT
        )
    """)

    valid = make_closed_row(
        "R56-POS36-VALID",
        symbol="VALID",
        pnl=8.5,
        r_multiple=1.7,
    )

    conn.execute(
        """
        INSERT INTO trades (
            uuid,
            status,
            close_time,
            exit_price,
            pnl,
            r_multiple,
            win_loss,
            holding_time,
            snapshot_close,
            snapshot_close_checksum,
            open_time,
            symbol,
            mode,
            asset_class
        )
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        valid,
    )

    tampered = list(
        make_closed_row(
            "R56-POS36-TAMPERED",
            symbol="TAMPER",
            pnl=8.5,
            r_multiple=1.7,
        )
    )
    tampered[4] = -999.0

    conn.execute(
        """
        INSERT INTO trades (
            uuid,
            status,
            close_time,
            exit_price,
            pnl,
            r_multiple,
            win_loss,
            holding_time,
            snapshot_close,
            snapshot_close_checksum,
            open_time,
            symbol,
            mode,
            asset_class
        )
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        tampered,
    )

    open_row = (
        "R56-POS36-OPEN",
        "OPEN",
        None,
        100.0,
        None,
        None,
        None,
        None,
        None,
        None,
        "2026-09-30T11:00:00",
        "OPEN",
        "PAPER",
        "EQUITY",
    )

    conn.execute(
        """
        INSERT INTO trades (
            uuid,
            status,
            close_time,
            exit_price,
            pnl,
            r_multiple,
            win_loss,
            holding_time,
            snapshot_close,
            snapshot_close_checksum,
            open_time,
            symbol,
            mode,
            asset_class
        )
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        open_row,
    )

    conn.commit()
    conn.close()


def isolated_connection_factory(db_path):
    def connection():
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn

    return connection


def expect_fail(callable_, fragment):
    try:
        callable_()
    except RuntimeError as exc:
        assert fragment in str(exc), (
            f"Unexpected validator failure: {exc}"
        )
        return
    raise AssertionError(
        "Expected fail-closed rejection did not occur"
    )


with tempfile.TemporaryDirectory() as td:
    db = Path(td) / "pos36.db"
    make_db(db)

    # ----------------------------------------------------------
    # 1. Direct validator — canonical record.
    # ----------------------------------------------------------
    valid_conn = sqlite3.connect(db)
    valid_conn.row_factory = sqlite3.Row
    valid_row = valid_conn.execute(
        "SELECT * FROM trades WHERE uuid = ?",
        ("R56-POS36-VALID",),
    ).fetchone()
    valid_conn.close()

    result = validate_closed_trade_record(valid_row)

    assert result["pnl"] == 8.5
    assert result["exit_price"] == 110.0
    assert result["r_multiple"] == 1.7

    print("R56_POS36_VALID_RECORD_ACCEPTED: PASS")

    # ----------------------------------------------------------
    # 2. Direct validator — tampered top-level PnL.
    # ----------------------------------------------------------
    tamper_conn = sqlite3.connect(db)
    tamper_conn.row_factory = sqlite3.Row
    tampered_row = tamper_conn.execute(
        "SELECT * FROM trades WHERE uuid = ?",
        ("R56-POS36-TAMPERED",),
    ).fetchone()
    tamper_conn.close()

    expect_fail(
        lambda: validate_closed_trade_record(tampered_row),
        "pnl conflicts with snapshot",
    )

    print("R56_POS36_DIRECT_TAMPER_REJECTED: PASS")

    # ----------------------------------------------------------
    # 3. Advanced analytics.
    # ----------------------------------------------------------
    old_aa = aa.get_connection
    aa.get_connection = isolated_connection_factory(db)

    try:
        valid_rows = aa.get_trades_with_filters(
            symbol="VALID",
            mode="PAPER",
            asset_class="EQUITY",
        )

        assert len(valid_rows) == 1
        assert valid_rows[0]["pnl"] == 8.5

        metrics = aa.compute_institutional_metrics(
            valid_rows
        )

        assert metrics["net_profit"] == 8.5
        assert metrics["avg_r"] == 1.7

        print(
            "R56_POS36_ADVANCED_VALIDATED_CLOSED_ACCEPTED: PASS"
        )

        expect_fail(
            lambda: aa.get_trades_with_filters(
                symbol="TAMPER",
                mode="PAPER",
                asset_class="EQUITY",
            ),
            "pnl conflicts with snapshot",
        )

        print(
            "R56_POS36_ADVANCED_TAMPER_REJECTED: PASS"
        )

    finally:
        aa.get_connection = old_aa

    # ----------------------------------------------------------
    # 4. Research report.
    # ----------------------------------------------------------
    old_rr = rr.get_connection
    rr.get_connection = isolated_connection_factory(db)

    try:
        expect_fail(
            lambda: rr.overall_performance(),
            "pnl conflicts with snapshot",
        )

        print(
            "R56_POS36_RESEARCH_REPORT_TAMPER_REJECTED: PASS"
        )

    finally:
        rr.get_connection = old_rr

    # ----------------------------------------------------------
    # 5. Trade forensics.
    # ----------------------------------------------------------
    old_tf = tf.get_connection
    tf.get_connection = isolated_connection_factory(db)

    try:
        valid_summary = tf.get_trade_summary(
            "R56-POS36-VALID"
        )

        assert valid_summary["status"] == "CLOSED"
        assert valid_summary["pnl"] == 8.5

        print(
            "R56_POS36_FORENSICS_VALID_CLOSED_ACCEPTED: PASS"
        )

        expect_fail(
            lambda: tf.get_trade_summary(
                "R56-POS36-TAMPERED"
            ),
            "pnl conflicts with snapshot",
        )

        print(
            "R56_POS36_FORENSICS_TAMPER_REJECTED: PASS"
        )

        open_summary = tf.get_trade_summary(
            "R56-POS36-OPEN"
        )

        assert open_summary["status"] == "OPEN"
        assert open_summary["uuid"] == "R56-POS36-OPEN"

        print(
            "R56_POS36_FORENSICS_OPEN_ROW_PRESERVED: PASS"
        )

    finally:
        tf.get_connection = old_tf


# --------------------------------------------------------------
# 6. Runtime-scope static certification.
# --------------------------------------------------------------
main_src = Path("main.py").read_text()
aa_src = Path("research/analytics_advanced.py").read_text()
rr_src = Path("research/research_report.py").read_text()
tf_src = Path("research/trade_forensics.py").read_text()

assert "validate_closed_trade_record" in main_src
assert "validate_closed_trade_record" in aa_src
assert "validate_closed_trade_record" in rr_src
assert "validate_closed_trade_record" in tf_src

assert "snapshot_close" in main_src
assert "snapshot_close_checksum" in main_src

print("R56_POS36_RUNTIME_BOUNDARIES_PRESENT: PASS")
print(
    "R56_POS36_SCOPE="
    "RUNTIME_REACHABLE_TERMINAL_RESULT_CONSUMERS"
)

print(
    "R56-POS-36-PERMANENT-WITNESS: PASS"
)
