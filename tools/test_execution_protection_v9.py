import os
import tempfile
from datetime import datetime, timezone


def _now():
    return datetime.now(timezone.utc).isoformat()


def _intent():
    now = _now()

    return {
        "authorization_id": "AUTH-V9-PROTECTION",
        "trade_uuid": "TRADE-V9-PROTECTION",
        "client_order_id": "CLIENT-V9-PROTECTION",
        "symbol": "TEST",
        "timeframe": "15m",
        "mode": "LIVE",
        "decision": "LONG",
        "quantity": 100.0,
        "requested_price": 100.0,
        "stop_loss": 95.0,
        "take_profit": 110.0,
        "status": "AUTHORIZED",
        "created_at": now,
        "updated_at": now,
    }


def _protection(
    *,
    protection_id,
    protection_type,
    broker_order_id,
):
    now = _now()

    return {
        "protection_id": protection_id,
        "authorization_id": "AUTH-V9-PROTECTION",
        "protection_type": protection_type,
        "target_index": 0,
        "broker_order_id": broker_order_id,
        "requested_qty": 100.0,
        "verified_qty": None,
        "requested_price": (
            95.0
            if protection_type == "STOP_LOSS"
            else 110.0
        ),
        "verified_price": None,
        "status": "PENDING",
        "created_at": now,
        "updated_at": now,
    }


def _broker(
    *,
    broker_order_id,
    protection_type,
    status="OPEN",
):
    price = (
        95.0
        if protection_type == "STOP_LOSS"
        else 110.0
    )

    return {
        "authorization_id": "AUTH-V9-PROTECTION",
        "symbol": "TEST",
        "instrument_token": "TEST|001",
        "broker_order_id": broker_order_id,
        "quantity": 100.0,
        "status": status,
        "order_type": (
            "SL"
            if protection_type == "STOP_LOSS"
            else "LIMIT"
        ),
        "transaction_type": "SELL",
        "trigger_price": (
            price
            if protection_type == "STOP_LOSS"
            else None
        ),
        "price": (
            None
            if protection_type == "STOP_LOSS"
            else price
        ),
    }


def _fresh_db():
    fd, path = tempfile.mkstemp(
        prefix="jaguar-v9-protection-",
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


def _seed(db):
    db.insert_execution_intent(_intent())

    db.update_execution_intent(
        "AUTH-V9-PROTECTION",
        status="SUBMITTED",
    )
    db.update_execution_intent(
        "AUTH-V9-PROTECTION",
        status="FILLED",
    )
    db.update_execution_intent(
        "AUTH-V9-PROTECTION",
        status="POSITION_RECONCILING",
    )
    db.update_execution_intent(
        "AUTH-V9-PROTECTION",
        status="PROTECTION_PENDING",
    )

    db.insert_execution_protection(
        _protection(
            protection_id="PROTECTION-SL",
            protection_type="STOP_LOSS",
            broker_order_id="PROTECT-1",
        )
    )

    db.insert_execution_protection(
        _protection(
            protection_id="PROTECTION-TP",
            protection_type="TAKE_PROFIT",
            broker_order_id="PROTECT-2",
        )
    )


def _both():
    return [
        _broker(
            broker_order_id="PROTECT-1",
            protection_type="STOP_LOSS",
        ),
        _broker(
            broker_order_id="PROTECT-2",
            protection_type="TAKE_PROFIT",
        ),
    ]


def main():
    path, db, recovery = _fresh_db()

    try:
        db.init_db()
        _seed(db)

        result = recovery.reconcile_execution_protection_group(
            "AUTH-V9-PROTECTION",
            instrument_token="TEST|001",
            broker_protections=_both(),
        )

        assert result["status"] == "RECONCILED"
        assert db.get_execution_intent(
            "AUTH-V9-PROTECTION"
        )["status"] == "RECONCILED"

        protections = db.list_execution_protections(
            "AUTH-V9-PROTECTION"
        )

        assert all(
            row["status"] == "VERIFIED"
            for row in protections
        )

        print("V9_PROTECTION_FULL_VERIFICATION: PASS")

        # Direction mismatch.
        path, db, recovery = _fresh_db()
        db.init_db()
        _seed(db)

        bad = _both()
        bad[0]["transaction_type"] = "BUY"

        result = recovery.reconcile_execution_protection_group(
            "AUTH-V9-PROTECTION",
            instrument_token="TEST|001",
            broker_protections=bad,
        )

        assert result["status"] == "HALTED"
        print("V9_PROTECTION_DIRECTION_FAIL_CLOSED: PASS")

        # Price mismatch.
        path, db, recovery = _fresh_db()
        db.init_db()
        _seed(db)

        bad = _both()
        bad[0]["trigger_price"] = 94.0

        result = recovery.reconcile_execution_protection_group(
            "AUTH-V9-PROTECTION",
            instrument_token="TEST|001",
            broker_protections=bad,
        )

        assert result["status"] == "HALTED"
        print("V9_PROTECTION_PRICE_FAIL_CLOSED: PASS")

        # Missing lineage member.
        path, db, recovery = _fresh_db()
        db.init_db()
        _seed(db)

        result = recovery.reconcile_execution_protection_group(
            "AUTH-V9-PROTECTION",
            instrument_token="TEST|001",
            broker_protections=[
                _broker(
                    broker_order_id="PROTECT-1",
                    protection_type="STOP_LOSS",
                ),
            ],
        )

        assert result["status"] == "HALTED"
        print("V9_PROTECTION_LINEAGE_SET_FAIL_CLOSED: PASS")

        # Inactive broker protection.
        path, db, recovery = _fresh_db()
        db.init_db()
        _seed(db)

        bad = _both()
        bad[0]["status"] = "COMPLETE"

        result = recovery.reconcile_execution_protection_group(
            "AUTH-V9-PROTECTION",
            instrument_token="TEST|001",
            broker_protections=bad,
        )

        assert result["status"] == "HALTED"
        print("V9_PROTECTION_INACTIVE_FAIL_CLOSED: PASS")

        # Quantity mismatch.
        path, db, recovery = _fresh_db()
        db.init_db()
        _seed(db)

        bad = _both()
        bad[0]["quantity"] = 99.0

        result = recovery.reconcile_execution_protection_group(
            "AUTH-V9-PROTECTION",
            instrument_token="TEST|001",
            broker_protections=bad,
        )

        assert result["status"] == "HALTED"
        print("V9_PROTECTION_QUANTITY_FAIL_CLOSED: PASS")

        # Parent state guard.
        path, db, recovery = _fresh_db()
        db.init_db()
        db.insert_execution_intent(_intent())

        result = recovery.reconcile_execution_protection_group(
            "AUTH-V9-PROTECTION",
            instrument_token="TEST|001",
            broker_protections=[],
        )

        assert result["status"] == "HALTED"
        print("V9_PROTECTION_STATE_GUARD_FAIL_CLOSED: PASS")

    finally:
        os.environ.pop("JAGUAR_DB_PATH", None)

        try:
            os.unlink(path)
        except FileNotFoundError:
            pass


if __name__ == "__main__":
    main()
