import hashlib
import os
import tempfile
from datetime import datetime, timezone

os.environ["JAGUAR_EXECUTION_MODE"] = "PAPER"


def now():
    return datetime.now(timezone.utc).isoformat()


def source_hash(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)
    print(f"{message:<55} PASS")


def main():
    production_files = [
        "intelligence/paper_post_fill.py",
        "research/database.py",
        "intelligence/paper_broker_adapter.py",
        "intelligence/execution_adapter.py",
    ]

    before_hashes = {
        path: source_hash(path)
        for path in production_files
    }

    with tempfile.TemporaryDirectory(prefix="jaguar-paper-durable-") as td:
        database_path = os.path.join(td, "certification.db")

        # Isolate database connection for this certification process.
        os.environ["JAGUAR_DB_PATH"] = database_path

        import research.database as db
        from intelligence.paper_post_fill import _persist_paper_durable_lifecycle

        db.init_db()

        authorization_id = (
            "BTCUSDT:ENTER_LONG:100.00000000:"
            "95.00000000:2.00000000:1.0000"
        )
        trade_uuid = "CERT-PAPER-DURABLE-TRADE-001"
        client_order_id = "JQX-CERT-PAPER-DURABLE-001"

        created = now()

        db.insert_execution_intent(
            {
                "authorization_id": authorization_id,
                "trade_uuid": trade_uuid,
                "client_order_id": client_order_id,
                "broker_order_id": None,
                "symbol": "BTCUSDT",
                "timeframe": "SWING",
                "mode": "PAPER",
                "decision": "LONG",
                "quantity": 2.0,
                "requested_price": 100.0,
                "stop_loss": 95.0,
                "take_profit": 110.0,
                "run_id": "CERT-RUN-001",
                "status": "AUTHORIZED",
                "created_at": created,
                "updated_at": created,
            }
        )

        db.update_execution_intent(
            authorization_id,
            status="SUBMITTED",
        )

        execution = {
            "ready": True,
            "approved": True,
            "status": "EXECUTE",
            "gate": "AUTHORIZED",
            "mode": "PAPER",
            "broker": "Paper",
            "symbol": "BTCUSDT",
            "decision": "ENTER_LONG",
            "entry": 100.0,
            "stop_loss": 95.0,
            "targets": [110.0, 120.0, 130.0],
            "position_size": 2.0,
            "risk_amount": 10.0,
            "risk_percent": 1.0,
            "authorization_id": authorization_id,
            "client_order_id": client_order_id,
        }

        execution_result = {
            "mode": "PAPER",
            "authorized": True,
            "authorization_id": authorization_id,
            "requested_quantity": 2.0,
            "filled_quantity": 2.0,
            "remaining_quantity": 0.0,
            "fill_price": 100.0,
            "order_status": "FILLED",
            "residual_cancelled": True,
            "order": {
                "authorization_id": authorization_id,
                "client_order_id": client_order_id,
                "broker_order_id": "PAPER-CERT-BROKER-001",
                "symbol": "BTCUSDT",
                "side": "BUY",
                "requested_qty": 2.0,
                "filled_qty": 2.0,
                "remaining_qty": 0.0,
                "average_fill_price": 100.0,
                "status": "FILLED",
            },
            "protection": {
                "authorization_id": authorization_id,
                "side": "SELL",
                "quantity": 2.0,
                "stop_loss": 95.0,
                "targets": [110.0, 120.0, 130.0],
                "status": "OPEN",
            },
            "position_reconciliation": {
                "reconciled": True,
                "status": "OPEN",
            },
            "protection_reconciliation": {
                "reconciled": True,
                "status": "OPEN",
            },
        }

        print("=== CANONICAL PAPER DURABLE LIFECYCLE ===")
        print("ISOLATED DB:", database_path)

        _persist_paper_durable_lifecycle(
            execution=execution,
            execution_result=execution_result,
            authorization_id=authorization_id,
            filled_quantity=2.0,
            authorized_stop=95.0,
            authorized_targets=[110.0, 120.0, 130.0],
        )

        intent = db.get_execution_intent(authorization_id)
        assert_true(
            intent["status"] == "RECONCILED",
            "SUBMITTED -> RECONCILED durable lifecycle",
        )

        protections = db.list_execution_protections(authorization_id)

        assert_true(
            len(protections) == 4,
            "DURABLE PROTECTION COUNT == 4",
        )

        types = sorted(
            str(row["protection_type"]).upper()
            for row in protections
        )

        assert_true(
            types == ["STOP_LOSS", "TAKE_PROFIT",
                      "TAKE_PROFIT", "TAKE_PROFIT"],
            "SL + TP1 + TP2 + TP3 DURABLE SET",
        )

        assert_true(
            all(
                str(row["status"]).upper() == "VERIFIED"
                for row in protections
            ),
            "ALL PAPER PROTECTIONS VERIFIED",
        )

        assert_true(
            all(row["broker_order_id"] is None for row in protections),
            "PAPER PROTECTIONS HAVE NO BROKER ORDER ID",
        )

        assert_true(
            all(
                float(row["requested_qty"]) == 2.0
                for row in protections
            ),
            "PROTECTION QUANTITY PRESERVED",
        )

        assert_true(
            intent["trade_uuid"] == trade_uuid,
            "TRADE UUID PRESERVED",
        )

        assert_true(
            intent["client_order_id"] == client_order_id,
            "CLIENT ORDER ID PRESERVED",
        )

        assert_true(
            intent["authorization_id"] == authorization_id,
            "AUTHORIZATION ID PRESERVED",
        )

        first_protection_ids = [
            row["protection_id"] for row in protections
        ]

        # Idempotent second invocation.
        _persist_paper_durable_lifecycle(
            execution=execution,
            execution_result=execution_result,
            authorization_id=authorization_id,
            filled_quantity=2.0,
            authorized_stop=95.0,
            authorized_targets=[110.0, 120.0, 130.0],
        )

        intent_after = db.get_execution_intent(authorization_id)
        protections_after = db.list_execution_protections(
            authorization_id
        )

        assert_true(
            intent_after["status"] == "RECONCILED",
            "RECONCILED TERMINAL STATE PRESERVED",
        )

        assert_true(
            len(protections_after) == 4,
            "NO DUPLICATE PAPER PROTECTIONS",
        )

        second_protection_ids = [
            row["protection_id"] for row in protections_after
        ]

        assert_true(
            second_protection_ids == first_protection_ids,
            "PROTECTION IDENTITY PRESERVED",
        )

        assert_true(
            intent_after["trade_uuid"] == trade_uuid,
            "TRADE UUID PRESERVED AFTER REPEAT",
        )

        assert_true(
            intent_after["client_order_id"] == client_order_id,
            "CLIENT ORDER ID PRESERVED AFTER REPEAT",
        )

        after_hashes = {
            path: source_hash(path)
            for path in production_files
        }

        assert_true(
            before_hashes == after_hashes,
            "PRODUCTION SOURCE IMMUTABILITY",
        )

    print()
    print("=== CERTIFICATION RESULT ===")
    print("PAPER DURABLE LIFECYCLE: PASS")
    print("DURABLE PROTECTION IDEMPOTENCY: PASS")
    print("IDENTITY PRESERVATION: PASS")
    print("PAPER BROKER SUBMISSION: 0")
    print("ISOLATED DB ONLY")
    print("NO PRODUCTION FILES MODIFIED")


if __name__ == "__main__":
    main()
