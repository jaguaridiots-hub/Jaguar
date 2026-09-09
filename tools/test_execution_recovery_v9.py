import os
import tempfile
from datetime import datetime, timezone


def _now():
    return datetime.now(timezone.utc).isoformat()


def _intent():
    now = _now()
    return {
        "authorization_id": "AUTH-V9-RECOVERY",
        "trade_uuid": "TRADE-V9-RECOVERY",
        "client_order_id": "CLIENT-V9-RECOVERY",
        "symbol": "TEST",
        "timeframe": "15m",
        "mode": "LIVE",
        "decision": "LONG",
        "quantity": 100.0,
        "requested_price": 100.0,
        "stop_loss": 95.0,
        "take_profit": 110.0,
        "run_id": "RUN-V9",
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
):
    now = _now()
    return {
        "order_lineage_id": lineage_id,
        "authorization_id": "AUTH-V9-RECOVERY",
        "trade_uuid": "TRADE-V9-RECOVERY",
        "client_order_id": "CLIENT-V9-RECOVERY",
        "broker_order_id": broker_order_id,
        "child_index": child_index,
        "instrument_token": "TEST|001",
        "transaction_type": "BUY",
        "requested_qty": requested_qty,
        "filled_qty": 0.0,
        "remaining_qty": requested_qty,
        "average_fill_price": None,
        "status": "SUBMITTED",
        "raw_status": "OPEN",
        "created_at": now,
        "updated_at": now,
    }


def _broker(
    *,
    broker_order_id,
    requested_qty,
    filled_qty,
    remaining_qty,
    status,
):
    return {
        "authorization_id": "AUTH-V9-RECOVERY",
        "client_order_id": "CLIENT-V9-RECOVERY",
        "broker_order_id": broker_order_id,
        "symbol": "TEST",
        "instrument_token": "TEST|001",
        "side": "BUY",
        "requested_qty": requested_qty,
        "filled_qty": filled_qty,
        "remaining_qty": remaining_qty,
        "average_fill_price": (
            100.0 if filled_qty > 0 else 0.0
        ),
        "status": status,
        "raw_status": status,
    }


def _fresh_db():
    fd, path = tempfile.mkstemp(
        prefix="jaguar-v9-recovery-",
        suffix=".db",
    )
    os.close(fd)

    os.environ["JAGUAR_DB_PATH"] = path

    import importlib
    import research.database as db
    import intelligence.execution_recovery as recovery

    db = importlib.reload(db)
    recovery = importlib.reload(recovery)

    return path, db, recovery


def _seed(db, *, authorization_id="AUTH-V9-RECOVERY"):
    db.insert_execution_intent(_intent())

    db.insert_execution_order(
        _order(
            lineage_id="LINEAGE-1",
            broker_order_id="BROKER-1",
            child_index=0,
            requested_qty=60.0,
        )
    )

    db.insert_execution_order(
        _order(
            lineage_id="LINEAGE-2",
            broker_order_id="BROKER-2",
            child_index=1,
            requested_qty=40.0,
        )
    )


def main():
    path, db, recovery = _fresh_db()

    try:
        db.init_db()

        # ------------------------------------------------------------
        # Exact multi-order fill
        # ------------------------------------------------------------
        _seed(db)

        result = recovery.reconcile_execution_order_group(
            "AUTH-V9-RECOVERY",
            broker_orders=[
                _broker(
                    broker_order_id="BROKER-1",
                    requested_qty=60.0,
                    filled_qty=60.0,
                    remaining_qty=0.0,
                    status="FILLED",
                ),
                _broker(
                    broker_order_id="BROKER-2",
                    requested_qty=40.0,
                    filled_qty=40.0,
                    remaining_qty=0.0,
                    status="FILLED",
                ),
            ],
        )

        assert result["status"] == "FILLED"

        parent = db.get_execution_intent(
            "AUTH-V9-RECOVERY"
        )
        assert parent["status"] == "FILLED"

        print("V9_RECOVERY_MULTI_ORDER_FILL: PASS")

        # ------------------------------------------------------------
        # Partial aggregate fill
        # ------------------------------------------------------------
        db_path = path
        os.unlink(db_path)

        path, db, recovery = _fresh_db()
        db.init_db()
        _seed(db)

        result = recovery.reconcile_execution_order_group(
            "AUTH-V9-RECOVERY",
            broker_orders=[
                _broker(
                    broker_order_id="BROKER-1",
                    requested_qty=60.0,
                    filled_qty=20.0,
                    remaining_qty=40.0,
                    status="PARTIAL",
                ),
                _broker(
                    broker_order_id="BROKER-2",
                    requested_qty=40.0,
                    filled_qty=0.0,
                    remaining_qty=40.0,
                    status="SUBMITTED",
                ),
            ],
        )

        assert result["status"] == "PARTIAL"
        parent = db.get_execution_intent(
            "AUTH-V9-RECOVERY"
        )
        assert parent["status"] == "PARTIAL"

        print("V9_RECOVERY_PARTIAL_AGGREGATION: PASS")

        # ------------------------------------------------------------
        # Duplicate observation identity
        # ------------------------------------------------------------
        db_path = path
        os.unlink(db_path)

        path, db, recovery = _fresh_db()
        db.init_db()
        _seed(db)

        result = recovery.reconcile_execution_order_group(
            "AUTH-V9-RECOVERY",
            broker_orders=[
                _broker(
                    broker_order_id="BROKER-1",
                    requested_qty=60.0,
                    filled_qty=60.0,
                    remaining_qty=0.0,
                    status="FILLED",
                ),
                _broker(
                    broker_order_id="BROKER-1",
                    requested_qty=40.0,
                    filled_qty=40.0,
                    remaining_qty=0.0,
                    status="FILLED",
                ),
            ],
        )

        assert result["status"] == "HALTED"
        print("V9_RECOVERY_DUPLICATE_ORDER_ID_FAIL_CLOSED: PASS")

        # ------------------------------------------------------------
        # Side mismatch
        # ------------------------------------------------------------
        db_path = path
        os.unlink(db_path)

        path, db, recovery = _fresh_db()
        db.init_db()
        _seed(db)

        bad_side = _broker(
            broker_order_id="BROKER-1",
            requested_qty=60.0,
            filled_qty=60.0,
            remaining_qty=0.0,
            status="FILLED",
        )
        bad_side["side"] = "SELL"

        result = recovery.reconcile_execution_order_group(
            "AUTH-V9-RECOVERY",
            broker_orders=[
                bad_side,
                _broker(
                    broker_order_id="BROKER-2",
                    requested_qty=40.0,
                    filled_qty=40.0,
                    remaining_qty=0.0,
                    status="FILLED",
                ),
            ],
        )

        assert result["status"] == "HALTED"
        print("V9_RECOVERY_DIRECTION_FAIL_CLOSED: PASS")

        # ------------------------------------------------------------
        # Aggregate requested quantity mismatch
        # ------------------------------------------------------------
        db_path = path
        os.unlink(db_path)

        path, db, recovery = _fresh_db()
        db.init_db()
        db.insert_execution_intent(_intent())

        db.insert_execution_order(
            _order(
                lineage_id="LINEAGE-1",
                broker_order_id="BROKER-1",
                child_index=0,
                requested_qty=50.0,
            )
        )

        db.insert_execution_order(
            _order(
                lineage_id="LINEAGE-2",
                broker_order_id="BROKER-2",
                child_index=1,
                requested_qty=40.0,
            )
        )

        result = recovery.reconcile_execution_order_group(
            "AUTH-V9-RECOVERY",
            broker_orders=[
                _broker(
                    broker_order_id="BROKER-1",
                    requested_qty=50.0,
                    filled_qty=50.0,
                    remaining_qty=0.0,
                    status="FILLED",
                ),
                _broker(
                    broker_order_id="BROKER-2",
                    requested_qty=40.0,
                    filled_qty=40.0,
                    remaining_qty=0.0,
                    status="FILLED",
                ),
            ],
        )

        assert result["status"] == "HALTED"
        print("V9_RECOVERY_AGGREGATE_QUANTITY_FAIL_CLOSED: PASS")

        # ------------------------------------------------------------
        # Incomplete fill with zero remaining quantity
        # ------------------------------------------------------------
        db_path = path
        os.unlink(db_path)

        path, db, recovery = _fresh_db()
        db.init_db()
        _seed(db)

        result = recovery.reconcile_execution_order_group(
            "AUTH-V9-RECOVERY",
            broker_orders=[
                _broker(
                    broker_order_id="BROKER-1",
                    requested_qty=60.0,
                    filled_qty=60.0,
                    remaining_qty=0.0,
                    status="FILLED",
                ),
                _broker(
                    broker_order_id="BROKER-2",
                    requested_qty=40.0,
                    filled_qty=0.0,
                    remaining_qty=0.0,
                    status="CANCELLED",
                ),
            ],
        )

        assert result["status"] == "HALTED"
        print("V9_RECOVERY_INCOMPLETE_ZERO_REMAINDER_FAIL_CLOSED: PASS")

        # ------------------------------------------------------------
        # Overfill
        # ------------------------------------------------------------
        db_path = path
        os.unlink(db_path)

        path, db, recovery = _fresh_db()
        db.init_db()
        _seed(db)

        result = recovery.reconcile_execution_order_group(
            "AUTH-V9-RECOVERY",
            broker_orders=[
                _broker(
                    broker_order_id="BROKER-1",
                    requested_qty=60.0,
                    filled_qty=61.0,
                    remaining_qty=-1.0,
                    status="FILLED",
                ),
                _broker(
                    broker_order_id="BROKER-2",
                    requested_qty=40.0,
                    filled_qty=40.0,
                    remaining_qty=0.0,
                    status="FILLED",
                ),
            ],
        )

        assert result["status"] == "HALTED"
        print("V9_RECOVERY_OVERFILL_FAIL_CLOSED: PASS")

        # ------------------------------------------------------------
        # All rejected
        # ------------------------------------------------------------
        db_path = path
        os.unlink(db_path)

        path, db, recovery = _fresh_db()
        db.init_db()
        _seed(db)

        result = recovery.reconcile_execution_order_group(
            "AUTH-V9-RECOVERY",
            broker_orders=[
                _broker(
                    broker_order_id="BROKER-1",
                    requested_qty=60.0,
                    filled_qty=0.0,
                    remaining_qty=60.0,
                    status="REJECTED",
                ),
                _broker(
                    broker_order_id="BROKER-2",
                    requested_qty=40.0,
                    filled_qty=0.0,
                    remaining_qty=40.0,
                    status="REJECTED",
                ),
            ],
        )

        assert result["status"] == "REJECTED"
        print("V9_RECOVERY_ALL_REJECTED: PASS")

    finally:
        os.environ.pop("JAGUAR_DB_PATH", None)
        try:
            os.unlink(path)
        except FileNotFoundError:
            pass


if __name__ == "__main__":
    main()
