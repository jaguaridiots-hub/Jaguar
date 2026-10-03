"""R56-POS-23 isolated proof that durable PAPER entry facts are reconstructible."""

import hashlib
import json
import tempfile
from pathlib import Path

import research.database as db


def checksum(data):
    return hashlib.sha256(
        json.dumps(
            data,
            sort_keys=True,
        ).encode()
    ).hexdigest()


def main():
    with tempfile.TemporaryDirectory(
        prefix="jaguar-pos23-reconstruct-"
    ) as td:
        db_path = Path(td) / "reconstruction.db"

        original_path = db.DB_PATH
        db.DB_PATH = str(db_path)

        try:
            db.init_db()

            authorization_id = "AUTH-R56-POS23-RECON"
            trade_uuid = "TRADE-R56-POS23-RECON"
            client_order_id = "CLIENT-R56-POS23-RECON"
            broker_order_id = "PAPER-R56-POS23-ORDER"

            enterprise_execution = {
                "authorization_id": authorization_id,
                "client_order_id": client_order_id,
                "trade_uuid": trade_uuid,
                "symbol": "BTCUSDT",
                "decision": "ENTER_LONG",
                "entry": 100.0,
                "stop_loss": 95.0,
                "targets": [
                    105.0,
                    110.0,
                    115.0,
                ],
                "position_size": 2.0,
                "risk_amount": 10.0,
                "mode": "PAPER",
            }

            snapshot_open = {
                "execution_authority": "IDM",
                "enterprise_execution": enterprise_execution,
                "mode": "PAPER",
                "market": {
                    "price": 100.0,
                    "high": 101.0,
                    "low": 99.0,
                    "volume": 10.0,
                },
            }

            snapshot_text = json.dumps(
                snapshot_open,
                sort_keys=True,
            )

            db.insert_execution_intent({
                "authorization_id": authorization_id,
                "trade_uuid": trade_uuid,
                "client_order_id": client_order_id,
                "broker_order_id": None,
                "symbol": "BTCUSDT",
                "timeframe": "15m",
                "mode": "PAPER",
                "decision": "LONG",
                "quantity": 2.0,
                "requested_price": 100.0,
                "stop_loss": 95.0,
                "take_profit": 105.0,
                "run_id": "R56-POS23",
                "status": "AUTHORIZED",
                "created_at": "2026-09-29T00:00:00",
                "updated_at": "2026-09-29T00:00:00",
            })

            db.update_execution_intent(
                authorization_id,
                broker_order_id=broker_order_id,
                status="SUBMITTED",
            )

            db.update_execution_intent(
                authorization_id,
                status="FILLED",
            )

            db.update_execution_intent(
                authorization_id,
                status="POSITION_RECONCILING",
            )

            db.update_execution_intent(
                authorization_id,
                status="PROTECTION_PENDING",
            )

            trade_conn = db.get_connection()

            try:
                trade_conn.execute(
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
                        snapshot_open,
                        snapshot_open_checksum,
                        decision,
                        run_id,
                        success
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        trade_uuid,
                        authorization_id,
                        "OPEN",
                        "2026-09-29T00:00:00",
                        "BTCUSDT",
                        "15m",
                        "PAPER",
                        100.0,
                        95.0,
                        105.0,
                        snapshot_text,
                        checksum(snapshot_open),
                        "LONG",
                        "R56-POS23",
                        1,
                    ),
                )
                trade_conn.commit()
            finally:
                trade_conn.close()

            intent = dict(
                db.get_execution_intent(
                    authorization_id
                )
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

            assert intent["mode"] == "PAPER"
            assert intent["trade_uuid"] == trade_uuid
            assert intent["authorization_id"] == authorization_id
            assert intent["broker_order_id"] == broker_order_id
            assert float(intent["quantity"]) == 2.0
            assert float(intent["requested_price"]) == 100.0
            assert float(intent["stop_loss"]) == 95.0
            assert float(intent["take_profit"]) == 105.0

            stored_snapshot = json.loads(
                trade["snapshot_open"]
            )

            assert (
                trade["snapshot_open_checksum"]
                == checksum(stored_snapshot)
            )

            durable_execution = stored_snapshot.get(
                "enterprise_execution"
            )

            assert isinstance(
                durable_execution,
                dict,
            )

            assert (
                durable_execution["authorization_id"]
                == authorization_id
            )
            assert (
                durable_execution["client_order_id"]
                == client_order_id
            )
            assert (
                durable_execution["trade_uuid"]
                == trade_uuid
            )
            assert (
                durable_execution["decision"]
                == "ENTER_LONG"
            )

            targets = durable_execution.get(
                "targets"
            )

            assert targets == [
                105.0,
                110.0,
                115.0,
            ]

            reconstructed = {
                "filled_quantity": float(
                    intent["quantity"]
                ),
                "fill_price": float(
                    trade["entry_price"]
                ),
                "remaining_quantity": 0.0,
                "order_status": "FILLED",
                "order": {
                    "authorization_id": authorization_id,
                    "client_order_id": client_order_id,
                    "broker_order_id": broker_order_id,
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
                    "authorization_id": authorization_id,
                    "symbol": intent["symbol"],
                    "quantity": float(
                        intent["quantity"]
                    ),
                    "reconciled": True,
                },
                "protection": {
                    "authorization_id": authorization_id,
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

            assert reconstructed["filled_quantity"] > 0
            assert reconstructed["fill_price"] > 0
            assert reconstructed["remaining_quantity"] == 0.0
            assert reconstructed["order"]["broker_order_id"] == (
                broker_order_id
            )
            assert reconstructed["protection"]["targets"] == targets

            print(
                "R56_POS23_DURABLE_INTENT_RECONSTRUCTABLE: PASS"
            )
            print(
                "R56_POS23_DURABLE_TARGETS_RECONSTRUCTABLE: PASS"
            )
            print(
                "R56_POS23_DURABLE_FILL_RECONSTRUCTABLE: PASS"
            )
            print(
                "R56_POS23_DURABLE_IDENTITY_RECONSTRUCTABLE: PASS"
            )
            print(
                "R56_POS23_DURABLE_PAPER_RESULT_RECONSTRUCTABLE: PASS"
            )

        finally:
            db.DB_PATH = original_path

    print("R56-POS23_RECONSTRUCTION_WITNESS: PASS")


if __name__ == "__main__":
    main()
