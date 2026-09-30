"""R56-POS-23 durable PAPER entry failure-consistency gate."""

from datetime import datetime
from pathlib import Path
import tempfile

import intelligence.paper_post_fill as pp
import research.database as db


def make_intent(auth, trade_uuid):
    now = datetime.now().isoformat()

    db.insert_execution_intent({
        "authorization_id": auth,
        "trade_uuid": trade_uuid,
        "client_order_id": f"CLIENT-{trade_uuid}",
        "symbol": "BTCUSDT",
        "timeframe": "15m",
        "mode": "PAPER",
        "decision": "LONG",
        "quantity": 1.0,
        "status": "AUTHORIZED",
        "created_at": now,
        "updated_at": now,
    })

    db.update_execution_intent(
        auth,
        broker_order_id=f"BROKER-{trade_uuid}",
        status="SUBMITTED",
    )


def result_for(auth):
    return {
        "requested_quantity": 1.0,
        "filled_quantity": 1.0,
        "fill_price": 100.0,
        "order_status": "FILLED",
        "remaining_quantity": 0.0,
        "order": {
            "authorization_id": auth,
            "status": "FILLED",
            "requested_qty": 1.0,
            "filled_qty": 1.0,
            "remaining_qty": 0.0,
        },
        "position_reconciliation": {
            "reconciled": True,
        },
        "protection": {
            "authorization_id": auth,
            "quantity": 1.0,
            "stop_loss": 95.0,
            "targets": [105.0, 110.0, 115.0],
        },
        "protection_reconciliation": {
            "reconciled": True,
        },
    }


def persist(auth):
    pp._persist_paper_durable_lifecycle(
        execution={},
        execution_result=result_for(auth),
        authorization_id=auth,
        filled_quantity=1.0,
        authorized_stop=95.0,
        authorized_targets=[105.0, 110.0, 115.0],
    )


def get_intent(auth):
    row = db.get_execution_intent(auth)

    assert row is not None, (
        f"Missing execution intent: {auth}"
    )

    return dict(row)


def get_protections(auth):
    return [
        dict(row)
        for row in db.list_execution_protections(auth)
    ]


def unresolved_count(symbol):
    conn = db.get_connection()

    try:
        row = conn.execute(
            """
            SELECT COUNT(*) AS n
            FROM execution_intents
            WHERE symbol = ?
              AND (
                  status IS NULL
                  OR status NOT IN (
                      'RECONCILED',
                      'REJECTED',
                      'CANCELLED'
                  )
              )
            """,
            (symbol,),
        ).fetchone()

        return int(row["n"])
    finally:
        conn.close()


def run_partial_protection_failure():
    auth = "AUTH-R56-POS23-A"
    trade_uuid = "TRADE-R56-POS23-A"

    make_intent(auth, trade_uuid)

    original_insert = pp.insert_execution_protection
    calls = {"count": 0}

    def fail_second_insert(data):
        calls["count"] += 1

        if calls["count"] == 2:
            raise RuntimeError(
                "INJECTED: second protection insert failure"
            )

        return original_insert(data)

    pp.insert_execution_protection = fail_second_insert

    try:
        try:
            persist(auth)
        except RuntimeError as exc:
            assert "second protection insert failure" in str(exc)
        else:
            raise AssertionError(
                "Expected injected second protection failure"
            )

        intent = get_intent(auth)
        protections = get_protections(auth)

        assert intent["status"] == "POSITION_RECONCILING"
        assert len(protections) == 1
        assert protections[0]["protection_type"] == "STOP_LOSS"
        assert protections[0]["status"] == "PENDING"

        assert unresolved_count("BTCUSDT") == 1

        print("R56_POS23_PARTIAL_PROTECTION_QUARANTINE: PASS")
        print("R56_POS23_PARTIAL_PROTECTION_BLOCKS_REENTRY: PASS")

    finally:
        pp.insert_execution_protection = original_insert

    # A second invocation must resume from the durable intermediate state,
    # not create a duplicate protection set.
    persist(auth)

    intent = get_intent(auth)
    protections = get_protections(auth)

    assert intent["status"] == "RECONCILED"
    assert len(protections) == 4

    assert all(
        str(row["status"]).strip().upper() == "VERIFIED"
        for row in protections
    )

    assert unresolved_count("BTCUSDT") == 0

    print("R56_POS23_PARTIAL_PROTECTION_RESUMABLE: PASS")
    print("R56_POS23_PARTIAL_PROTECTION_IDEMPOTENT: PASS")


def run_final_reconciled_failure():
    auth = "AUTH-R56-POS23-B"
    trade_uuid = "TRADE-R56-POS23-B"

    make_intent(auth, trade_uuid)

    original_update = pp.update_execution_intent

    def fail_reconciled(auth_id, **kwargs):
        if kwargs.get("status") == "RECONCILED":
            raise RuntimeError(
                "INJECTED: final RECONCILED persistence failure"
            )

        return original_update(auth_id, **kwargs)

    pp.update_execution_intent = fail_reconciled

    try:
        try:
            persist(auth)
        except RuntimeError as exc:
            assert "final RECONCILED persistence failure" in str(exc)
        else:
            raise AssertionError(
                "Expected injected final RECONCILED failure"
            )

        intent = get_intent(auth)
        protections = get_protections(auth)

        assert intent["status"] == "PROTECTION_PENDING"
        assert len(protections) == 4

        assert all(
            str(row["status"]).strip().upper() == "VERIFIED"
            for row in protections
        )

        assert unresolved_count("BTCUSDT") == 1

        print("R56_POS23_FINAL_RECONCILED_FAILURE_QUARANTINE: PASS")
        print("R56_POS23_FINAL_RECONCILED_FAILURE_BLOCKS_REENTRY: PASS")

    finally:
        pp.update_execution_intent = original_update

    # The persisted PROTECTION_PENDING state must be resumable.
    persist(auth)

    intent = get_intent(auth)
    protections = get_protections(auth)

    assert intent["status"] == "RECONCILED"
    assert len(protections) == 4

    assert all(
        str(row["status"]).strip().upper() == "VERIFIED"
        for row in protections
    )

    assert unresolved_count("BTCUSDT") == 0

    print("R56_POS23_FINAL_RECONCILED_FAILURE_RESUMABLE: PASS")
    print("R56_POS23_FINAL_RECONCILED_FAILURE_IDEMPOTENT: PASS")


def main():
    Path(".jaguar_audit").mkdir(exist_ok=True)

    with tempfile.TemporaryDirectory(
        prefix="jaguar-pos23-"
    ) as td:
        temp_db = Path(td) / "pos23.db"

        original_db_path = db.DB_PATH
        db.DB_PATH = str(temp_db)

        try:
            db.init_db()

            run_partial_protection_failure()
            run_final_reconciled_failure()

            conn = db.get_connection()

            try:
                print()
                print("R56_POS23_ISOLATED_DB_COUNTS:")

                for table in (
                    "trades",
                    "execution_intents",
                    "execution_orders",
                    "execution_protection",
                    "execution_submission_journal",
                ):
                    row = conn.execute(
                        f"SELECT COUNT(*) AS n FROM {table}"
                    ).fetchone()

                    print(
                        f"{table}: {int(row['n'])}"
                    )

            finally:
                conn.close()

        finally:
            db.DB_PATH = original_db_path

    print()
    print("R56-POS-23_FAILURE_MATRIX_COMPLETE")


if __name__ == "__main__":
    main()
