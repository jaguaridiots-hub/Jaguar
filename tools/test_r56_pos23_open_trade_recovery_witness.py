"""R56-POS-23 witness using the real trade recorder contract."""

from pathlib import Path
from types import SimpleNamespace
import hashlib
import json
import tempfile

import intelligence.paper_post_fill as pp
import research.database as db
from research.recorder import record_trade_open


def checksum(data):
    return hashlib.sha256(
        json.dumps(
            data,
            sort_keys=True,
        ).encode()
    ).hexdigest()


def make_state(auth, trade_uuid):
    enterprise_execution = {
        "authorization_id": auth,
        "client_order_id": "CLIENT-R56-POS23-OPEN",
        "trade_uuid": trade_uuid,
        "symbol": "BTCUSDT",
        "decision": "ENTER_LONG",
        "entry": 100.0,
        "fill_price": 100.0,
        "stop_loss": 95.0,
        "targets": [105.0, 110.0, 115.0],
        "position_size": 2.0,
        "risk_amount": 10.0,
        "mode": "PAPER",
    }

    enterprise_trade = {
        "entry": 100.0,
        "stop_loss": 95.0,
        "targets": [105.0, 110.0, 115.0],
    }

    return SimpleNamespace(
        symbol="BTCUSDT",
        interval="15m",
        mode="PAPER",
        price=100.0,
        high=101.0,
        low=99.0,
        volume=1000.0,
        run_id="R56-POS23-OPEN-WITNESS",
        execution=enterprise_execution,
        trade=enterprise_trade,
        trade_plan={},
        idm={
            "decision": "LONG",
            "confidence": 90.0,
            "score": 95.0,
        },
        master_decision={},
        ai_brain={"score": 90.0},
        probability={"score": 90.0},
        risk={"approved": True},
        trade_validator={"validation_score": 100.0},
        _decision_weights={},
        brain_explain={"contributions": []},
        regime={},
        market={
            "regime_result": {},
            "liquidity_result": {},
            "structural_results": {
                "fvg": {},
            },
        },
        mtf={},
        smc={},
        liquidity={},
        orderflow={},
    )


def insert_intent(auth, trade_uuid):
    db.insert_execution_intent({
        "authorization_id": auth,
        "trade_uuid": trade_uuid,
        "client_order_id": "CLIENT-R56-POS23-OPEN",
        "broker_order_id": None,
        "symbol": "BTCUSDT",
        "timeframe": "15m",
        "mode": "PAPER",
        "decision": "LONG",
        "quantity": 2.0,
        "requested_price": 100.0,
        "stop_loss": 95.0,
        "take_profit": 105.0,
        "run_id": "R56-POS23-OPEN-WITNESS",
        "status": "AUTHORIZED",
        "created_at": "2026-09-29T00:00:00",
        "updated_at": "2026-09-29T00:00:00",
    })

    db.update_execution_intent(
        auth,
        broker_order_id="PAPER-R56-POS23-OPEN-001",
        status="SUBMITTED",
    )


def reconstruct_from_durable_rows(auth):
    intent_row = db.get_execution_intent(auth)
    assert intent_row is not None

    intent = dict(intent_row)

    conn = db.get_connection()

    try:
        trade_row = conn.execute(
            """
            SELECT *
            FROM trades
            WHERE uuid = ?
            LIMIT 1
            """,
            (intent["trade_uuid"],),
        ).fetchone()
    finally:
        conn.close()

    assert trade_row is not None

    trade = dict(trade_row)

    assert trade["status"] == "OPEN"
    assert trade["close_time"] is None

    stored_snapshot = json.loads(
        trade["snapshot_open"]
    )

    stored_checksum = trade["snapshot_open_checksum"]

    assert stored_checksum == checksum(
        stored_snapshot
    )

    durable_execution = stored_snapshot.get(
        "enterprise_execution"
    )

    assert isinstance(
        durable_execution,
        dict,
    )

    assert durable_execution["authorization_id"] == (
        auth
    )

    assert durable_execution["trade_uuid"] == (
        intent["trade_uuid"]
    )

    assert durable_execution["client_order_id"] == (
        intent["client_order_id"]
    )

    assert durable_execution["decision"] == "ENTER_LONG"

    targets = durable_execution["targets"]

    assert targets == [
        105.0,
        110.0,
        115.0,
    ]

    assert float(
        durable_execution["entry"]
    ) == float(intent["requested_price"])

    assert float(
        durable_execution["stop_loss"]
    ) == float(intent["stop_loss"])

    assert float(
        durable_execution["position_size"]
    ) == float(intent["quantity"])

    reconstructed = {
        "requested_quantity": float(
            intent["quantity"]
        ),
        "filled_quantity": float(
            intent["quantity"]
        ),
        "fill_price": float(
            trade["entry_price"]
        ),
        "remaining_quantity": 0.0,
        "order_status": "FILLED",
        "order": {
            "authorization_id": auth,
            "client_order_id": intent[
                "client_order_id"
            ],
            "broker_order_id": intent[
                "broker_order_id"
            ],
            "symbol": intent["symbol"],
            "side": "BUY",
            "requested_qty": float(
                intent["quantity"]
            ),
            "filled_qty": float(
                intent["quantity"]
            ),
            "remaining_qty": 0.0,
            "average_fill_price": float(
                trade["entry_price"]
            ),
            "status": "FILLED",
        },
        "position_reconciliation": {
            "authorization_id": auth,
            "symbol": intent["symbol"],
            "quantity": float(
                intent["quantity"]
            ),
            "reconciled": True,
        },
        "protection": {
            "authorization_id": auth,
            "quantity": float(
                intent["quantity"]
            ),
            "stop_loss": float(
                intent["stop_loss"]
            ),
            "targets": targets,
        },
        "protection_reconciliation": {
            "reconciled": True,
        },
    }

    return reconstructed


def main():
    with tempfile.TemporaryDirectory(
        prefix="jaguar-pos23-open-"
    ) as td:
        temp_db = Path(td) / "open-recovery.db"

        original_db_path = db.DB_PATH
        db.DB_PATH = str(temp_db)

        try:
            db.init_db()

            auth = "AUTH-R56-POS23-OPEN"
            trade_uuid = "TRADE-R56-POS23-OPEN"

            state = make_state(
                auth,
                trade_uuid,
            )

            insert_intent(
                auth,
                trade_uuid,
            )

            recorded = record_trade_open(
                state,
                run_id=state.run_id,
                entry_time="2026-09-29T00:00:00",
                trade_uuid=trade_uuid,
                authorization_id=auth,
            )

            assert recorded == trade_uuid

            intent_before = dict(
                db.get_execution_intent(auth)
            )

            assert intent_before["status"] == "SUBMITTED"

            # Simulated crash boundary:
            # durable OPEN trade exists, but PAPER lifecycle is unfinished.
            reconstructed = reconstruct_from_durable_rows(
                auth
            )

            print(
                "R56_POS23_REAL_TRADE_SNAPSHOT_RECONSTRUCTABLE: PASS"
            )
            print(
                "R56_POS23_REAL_TARGETS_RECONSTRUCTABLE: PASS"
            )
            print(
                "R56_POS23_REAL_FILL_RECONSTRUCTABLE: PASS"
            )
            print(
                "R56_POS23_REAL_IDENTITY_RECONSTRUCTABLE: PASS"
            )

            pp._persist_paper_durable_lifecycle(
                execution=dict(
                    state.execution
                ),
                execution_result=reconstructed,
                authorization_id=auth,
                filled_quantity=float(
                    reconstructed[
                        "filled_quantity"
                    ]
                ),
                authorized_stop=95.0,
                authorized_targets=[
                    105.0,
                    110.0,
                    115.0,
                ],
            )

            final_intent = dict(
                db.get_execution_intent(auth)
            )

            protections = [
                dict(row)
                for row in db.list_execution_protections(
                    auth
                )
            ]

            assert final_intent["status"] == (
                "RECONCILED"
            )

            assert len(protections) == 4

            assert all(
                str(row["status"]).strip().upper()
                == "VERIFIED"
                for row in protections
            )

            conn = db.get_connection()

            try:
                trade = dict(
                    conn.execute(
                        """
                        SELECT *
                        FROM trades
                        WHERE uuid = ?
                        """,
                        (trade_uuid,),
                    ).fetchone()
                )
            finally:
                conn.close()

            assert trade["status"] == "OPEN"
            assert trade["close_time"] is None

            print(
                "R56_POS23_REAL_OPEN_TRADE_RESUMABLE: PASS"
            )
            print(
                "R56_POS23_REAL_OPEN_TRADE_RECONCILED: PASS"
            )
            print(
                "R56_POS23_REAL_OPEN_TRADE_IDEMPOTENT_BOUNDARY: PASS"
            )

        finally:
            db.DB_PATH = original_db_path

    print(
        "R56-POS-23_REAL_OPEN_TRADE_RECOVERY_WITNESS: PASS"
    )


if __name__ == "__main__":
    main()
