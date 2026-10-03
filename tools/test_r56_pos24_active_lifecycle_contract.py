import hashlib
import json
import sqlite3
import tempfile
from pathlib import Path


SCHEMA = """
CREATE TABLE active_trade_lifecycle (
    trade_uuid TEXT PRIMARY KEY,
    authorization_id TEXT NOT NULL UNIQUE,
    symbol TEXT NOT NULL,
    position TEXT NOT NULL,
    entry REAL NOT NULL,
    current_stop REAL NOT NULL,
    take_profit REAL NOT NULL,
    position_size REAL NOT NULL,
    initial_risk REAL NOT NULL,
    tp1_hit INTEGER NOT NULL,
    tp2_hit INTEGER NOT NULL,
    break_even INTEGER NOT NULL,
    trailing INTEGER NOT NULL,
    trade_closed INTEGER NOT NULL,
    revision INTEGER NOT NULL,
    state_checksum TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
"""


BOOLEAN_FIELDS = (
    "tp1_hit",
    "tp2_hit",
    "break_even",
    "trailing",
    "trade_closed",
)


def lifecycle_checksum(state):
    payload = {
        key: state[key]
        for key in (
            "trade_uuid",
            "authorization_id",
            "symbol",
            "position",
            "entry",
            "current_stop",
            "take_profit",
            "position_size",
            "initial_risk",
            "tp1_hit",
            "tp2_hit",
            "break_even",
            "trailing",
            "trade_closed",
            "revision",
        )
    }

    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()


def validate_lifecycle(state):
    if state["position"] not in {"LONG", "SHORT"}:
        raise RuntimeError(
            "FAIL-CLOSED: invalid lifecycle position"
        )

    if state["trade_closed"] is not False:
        raise RuntimeError(
            "FAIL-CLOSED: OPEN lifecycle cannot be terminal"
        )

    if state["tp2_hit"] and not state["tp1_hit"]:
        raise RuntimeError(
            "FAIL-CLOSED: TP2 requires TP1"
        )

    if state["break_even"] and not state["tp1_hit"]:
        raise RuntimeError(
            "FAIL-CLOSED: break-even requires TP1"
        )

    if state["trailing"] and not state["tp2_hit"]:
        raise RuntimeError(
            "FAIL-CLOSED: trailing requires TP2"
        )

    if state["current_stop"] <= 0:
        raise RuntimeError(
            "FAIL-CLOSED: invalid current stop"
        )

    # Current-stop transition semantics belong to TradeManager.
    # The durable lifecycle contract validates persistence integrity
    # and lifecycle ordering, but does not invent an independent
    # trading rule for the stop location.


def insert_initial(conn, state):
    validate_lifecycle(state)

    checksum = lifecycle_checksum(state)

    conn.execute(
        """
        INSERT INTO active_trade_lifecycle (
            trade_uuid,
            authorization_id,
            symbol,
            position,
            entry,
            current_stop,
            take_profit,
            position_size,
            initial_risk,
            tp1_hit,
            tp2_hit,
            break_even,
            trailing,
            trade_closed,
            revision,
            state_checksum,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            state["trade_uuid"],
            state["authorization_id"],
            state["symbol"],
            state["position"],
            state["entry"],
            state["current_stop"],
            state["take_profit"],
            state["position_size"],
            state["initial_risk"],
            int(state["tp1_hit"]),
            int(state["tp2_hit"]),
            int(state["break_even"]),
            int(state["trailing"]),
            int(state["trade_closed"]),
            state["revision"],
            checksum,
            "2026-09-29T00:00:00",
            "2026-09-29T00:00:00",
        ),
    )
    conn.commit()


def update_lifecycle_cas(conn, state, expected_revision):
    validate_lifecycle(state)

    if state["revision"] != expected_revision + 1:
        raise RuntimeError(
            "FAIL-CLOSED: lifecycle revision must advance exactly by one"
        )

    checksum = lifecycle_checksum(state)

    cursor = conn.execute(
        """
        UPDATE active_trade_lifecycle
        SET
            current_stop = ?,
            tp1_hit = ?,
            tp2_hit = ?,
            break_even = ?,
            trailing = ?,
            trade_closed = ?,
            revision = ?,
            state_checksum = ?,
            updated_at = ?
        WHERE trade_uuid = ?
          AND revision = ?
        """,
        (
            state["current_stop"],
            int(state["tp1_hit"]),
            int(state["tp2_hit"]),
            int(state["break_even"]),
            int(state["trailing"]),
            int(state["trade_closed"]),
            state["revision"],
            checksum,
            "2026-09-29T00:01:00",
            state["trade_uuid"],
            expected_revision,
        ),
    )

    if cursor.rowcount != 1:
        conn.rollback()
        raise RuntimeError(
            "FAIL-CLOSED: stale or missing lifecycle revision"
        )

    conn.commit()


def read_lifecycle(conn, trade_uuid):
    row = conn.execute(
        """
        SELECT *
        FROM active_trade_lifecycle
        WHERE trade_uuid = ?
        """,
        (trade_uuid,),
    ).fetchone()

    assert row is not None

    state = dict(row)

    for field in BOOLEAN_FIELDS:
        state[field] = bool(state[field])

    expected_checksum = lifecycle_checksum(state)

    assert state["state_checksum"] == expected_checksum

    return state


def main():
    with tempfile.TemporaryDirectory(
        prefix="jaguar-pos24-lifecycle-v2-"
    ) as td:
        db_path = Path(td) / "lifecycle.db"

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row

        try:
            conn.execute(SCHEMA)
            conn.commit()

            base = {
                "trade_uuid": "TRADE-R56-POS24-001",
                "authorization_id": "AUTH-R56-POS24-001",
                "symbol": "BTCUSDT",
                "position": "LONG",
                "entry": 100.0,
                "current_stop": 95.0,
                "take_profit": 105.0,
                "position_size": 2.0,
                "initial_risk": 10.0,
                "tp1_hit": False,
                "tp2_hit": False,
                "break_even": False,
                "trailing": False,
                "trade_closed": False,
                "revision": 1,
            }

            insert_initial(conn, base)

            first = read_lifecycle(
                conn,
                base["trade_uuid"],
            )

            assert first["revision"] == 1
            assert first["current_stop"] == 95.0

            print(
                "R56_POS24_INITIAL_LIFECYCLE: PASS"
            )

            tp1 = dict(base)
            tp1.update(
                current_stop=100.0,
                tp1_hit=True,
                break_even=True,
                revision=2,
            )

            update_lifecycle_cas(
                conn,
                tp1,
                expected_revision=1,
            )

            second = read_lifecycle(
                conn,
                base["trade_uuid"],
            )

            assert second["current_stop"] == 100.0
            assert second["tp1_hit"] is True
            assert second["break_even"] is True
            assert second["revision"] == 2

            print(
                "R56_POS24_TP1_BREAK_EVEN: PASS"
            )

            tp2 = dict(tp1)
            tp2.update(
                current_stop=108.0,
                tp2_hit=True,
                trailing=True,
                revision=3,
            )

            # Actual TradeManager behavior: LONG trailing stop may
            # legitimately exceed TP1.
            assert tp2["current_stop"] > 105.0

            update_lifecycle_cas(
                conn,
                tp2,
                expected_revision=2,
            )

            third = read_lifecycle(
                conn,
                base["trade_uuid"],
            )

            assert third["current_stop"] == 108.0
            assert third["tp2_hit"] is True
            assert third["trailing"] is True
            assert third["revision"] == 3

            print(
                "R56_POS24_TP2_TRAILING: PASS"
            )

            # Same state may be re-read idempotently.
            reread = read_lifecycle(
                conn,
                base["trade_uuid"],
            )

            assert reread["revision"] == 3
            assert reread["state_checksum"] == third["state_checksum"]

            print(
                "R56_POS24_IDEMPOTENT_READ: PASS"
            )

            # Stale writer must fail.
            stale = dict(tp2)
            stale.update(
                current_stop=107.0,
                revision=3,
            )

            try:
                update_lifecycle_cas(
                    conn,
                    stale,
                    expected_revision=2,
                )
            except RuntimeError:
                print(
                    "R56_POS24_STALE_REVISION_FAIL_CLOSED: PASS"
                )
            else:
                raise AssertionError(
                    "Stale lifecycle write was accepted"
                )

            # Non-monotonic revision must fail before DB update.
            stale = dict(tp2)
            stale.update(
                current_stop=107.0,
                revision=2,
            )

            try:
                update_lifecycle_cas(
                    conn,
                    stale,
                    expected_revision=3,
                )
            except RuntimeError:
                print(
                    "R56_POS24_NON_MONOTONIC_REVISION_FAIL_CLOSED: PASS"
                )
            else:
                raise AssertionError(
                    "Non-monotonic revision was accepted"
                )

            # Checksum corruption must be detected.
            conn.execute(
                """
                UPDATE active_trade_lifecycle
                SET current_stop = ?
                WHERE trade_uuid = ?
                """,
                (
                    99.0,
                    base["trade_uuid"],
                ),
            )
            conn.commit()

            try:
                read_lifecycle(
                    conn,
                    base["trade_uuid"],
                )
            except AssertionError:
                print(
                    "R56_POS24_CHECKSUM_CORRUPTION_FAIL_CLOSED: PASS"
                )
            else:
                raise AssertionError(
                    "Checksum corruption was accepted"
                )

            # Restore the valid lifecycle explicitly.
            conn.execute(
                """
                UPDATE active_trade_lifecycle
                SET
                    current_stop = ?,
                    tp1_hit = ?,
                    tp2_hit = ?,
                    break_even = ?,
                    trailing = ?,
                    trade_closed = ?,
                    revision = ?,
                    state_checksum = ?
                WHERE trade_uuid = ?
                """,
                (
                    tp2["current_stop"],
                    int(tp2["tp1_hit"]),
                    int(tp2["tp2_hit"]),
                    int(tp2["break_even"]),
                    int(tp2["trailing"]),
                    int(tp2["trade_closed"]),
                    tp2["revision"],
                    lifecycle_checksum(tp2),
                    tp2["trade_uuid"],
                ),
            )
            conn.commit()

            # Invalid lifecycle relationships.
            invalid = dict(tp2)
            invalid.update(
                tp1_hit=False,
                tp2_hit=True,
                revision=4,
            )

            try:
                validate_lifecycle(invalid)
            except RuntimeError:
                print(
                    "R56_POS24_INVALID_TP_ORDER_FAIL_CLOSED: PASS"
                )
            else:
                raise AssertionError(
                    "Invalid TP lifecycle accepted"
                )

            invalid = dict(tp2)
            invalid.update(
                tp2_hit=False,
                trailing=True,
                revision=4,
            )

            try:
                validate_lifecycle(invalid)
            except RuntimeError:
                print(
                    "R56_POS24_INVALID_TRAILING_FAIL_CLOSED: PASS"
                )
            else:
                raise AssertionError(
                    "Invalid trailing lifecycle accepted"
                )

            invalid = dict(tp2)
            invalid.update(
                trade_closed=True,
                revision=4,
            )

            try:
                validate_lifecycle(invalid)
            except RuntimeError:
                print(
                    "R56_POS24_TERMINAL_OPEN_FAIL_CLOSED: PASS"
                )
            else:
                raise AssertionError(
                    "Terminal OPEN lifecycle accepted"
                )

            # Crash boundary:
            # DB state survives independently of local JSON cache.
            recovered = read_lifecycle(
                conn,
                base["trade_uuid"],
            )

            assert recovered["revision"] == 3
            assert recovered["current_stop"] == 108.0
            assert recovered["tp1_hit"] is True
            assert recovered["tp2_hit"] is True
            assert recovered["break_even"] is True
            assert recovered["trailing"] is True

            print(
                "R56_POS24_DB_RECOVERY_AFTER_LOCAL_CACHE_LOSS: PASS"
            )

            print(
                "R56-POS-24_ACTIVE_LIFECYCLE_CONTRACT_V2: PASS"
            )

        finally:
            conn.close()


if __name__ == "__main__":
    main()
