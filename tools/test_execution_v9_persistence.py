import os
import tempfile
from datetime import datetime, timezone


def _now():
    return datetime.now(timezone.utc).isoformat()


def _intent():
    now = _now()
    return {
        "authorization_id": "AUTH-V9-TEST",
        "trade_uuid": "TRADE-V9-TEST",
        "client_order_id": "JGX-V9-TEST",
        "symbol": "TEST",
        "timeframe": "15m",
        "mode": "LIVE",
        "decision": "LONG",
        "quantity": 100.0,
        "requested_price": 100.0,
        "stop_loss": 95.0,
        "take_profit": 110.0,
        "run_id": "RUN-V9-TEST",
        "status": "AUTHORIZED",
        "created_at": now,
        "updated_at": now,
    }


def _order(
    *,
    lineage_id,
    broker_order_id,
    child_index,
    requested_qty,
    filled_qty,
    remaining_qty,
    status,
):
    now = _now()
    return {
        "order_lineage_id": lineage_id,
        "authorization_id": "AUTH-V9-TEST",
        "trade_uuid": "TRADE-V9-TEST",
        "client_order_id": "JGX-V9-TEST",
        "broker_order_id": broker_order_id,
        "child_index": child_index,
        "instrument_token": "TEST|001",
        "transaction_type": "BUY",
        "requested_qty": requested_qty,
        "filled_qty": filled_qty,
        "remaining_qty": remaining_qty,
        "average_fill_price": 100.0,
        "status": status,
        "raw_status": "OPEN",
        "created_at": now,
        "updated_at": now,
    }


def main():
    fd, db_path = tempfile.mkstemp(prefix="jaguar-v9-", suffix=".db")
    os.close(fd)

    try:
        os.environ["JAGUAR_DB_PATH"] = db_path

        import research.database as db

        db.init_db()
        db.insert_execution_intent(_intent())

        db.insert_execution_order(
            _order(
                lineage_id="LINEAGE-1",
                broker_order_id="BROKER-1",
                child_index=0,
                requested_qty=60.0,
                filled_qty=20.0,
                remaining_qty=40.0,
                status="PARTIAL",
            )
        )

        db.insert_execution_order(
            _order(
                lineage_id="LINEAGE-2",
                broker_order_id="BROKER-2",
                child_index=1,
                requested_qty=40.0,
                filled_qty=0.0,
                remaining_qty=40.0,
                status="SUBMITTED",
            )
        )

        orders = db.list_execution_orders(
            "AUTH-V9-TEST"
        )

        assert len(orders) == 2
        assert orders[0]["child_index"] == 0
        assert orders[1]["child_index"] == 1

        db.update_execution_order(
            "LINEAGE-1",
            status="FILLED",
            filled_qty=60.0,
            remaining_qty=0.0,
            average_fill_price=101.0,
        )

        order = db.get_execution_order(
            "LINEAGE-1"
        )

        assert order["status"] == "FILLED"
        assert float(order["filled_qty"]) == 60.0
        assert float(order["remaining_qty"]) == 0.0

        db.insert_execution_protection({
            "protection_id": "PROTECTION-1",
            "authorization_id": "AUTH-V9-TEST",
            "protection_type": "STOP_LOSS",
            "target_index": None,
            "broker_order_id": None,
            "requested_qty": 100.0,
            "verified_qty": None,
            "requested_price": 95.0,
            "verified_price": None,
            "status": "PENDING",
            "created_at": _now(),
            "updated_at": _now(),
        })

        db.update_execution_protection(
            "PROTECTION-1",
            broker_order_id="PROTECTION-BROKER-1",
            verified_qty=100.0,
            verified_price=95.0,
            status="VERIFIED",
        )

        protection = db.get_execution_protection(
            "PROTECTION-1"
        )

        assert protection["status"] == "VERIFIED"
        assert (
            protection["broker_order_id"]
            == "PROTECTION-BROKER-1"
        )
        assert float(
            protection["verified_qty"]
        ) == 100.0

        try:
            db.insert_execution_order(
                _order(
                    lineage_id="LINEAGE-BAD",
                    broker_order_id="BROKER-BAD",
                    child_index=2,
                    requested_qty=10.0,
                    filled_qty=8.0,
                    remaining_qty=1.0,
                    status="PARTIAL",
                )
            )
        except ValueError:
            pass
        else:
            raise AssertionError(
                "quantity conservation failure was accepted"
            )

        try:
            db.update_execution_order(
                "LINEAGE-1",
                filled_qty=61.0,
                remaining_qty=0.0,
            )
        except RuntimeError:
            pass
        else:
            raise AssertionError(
                "filled quantity overflow was accepted"
            )

        try:
            db.update_execution_protection(
                "PROTECTION-1",
                broker_order_id="PROTECTION-BROKER-2",
            )
        except RuntimeError:
            pass
        else:
            raise AssertionError(
                "protection broker identity mutation was accepted"
            )

        try:
            db.update_execution_protection(
                "PROTECTION-1",
                status="PENDING",
            )
        except RuntimeError:
            pass
        else:
            raise AssertionError(
                "terminal protection regression was accepted"
            )

        print("V9_PERSISTENCE_ORDER_LINEAGE: PASS")
        print("V9_PERSISTENCE_PARTIAL_FILL: PASS")
        print("V9_PERSISTENCE_PROTECTION: PASS")
        print("V9_PERSISTENCE_QUANTITY_INVARIANT: PASS")
        print("V9_PERSISTENCE_IDENTITY_IMMUTABILITY: PASS")
        print("V9_PERSISTENCE_TERMINAL_IMMUTABILITY: PASS")

    finally:
        os.environ.pop("JAGUAR_DB_PATH", None)
        try:
            os.unlink(db_path)
        except FileNotFoundError:
            pass


if __name__ == "__main__":
    main()
