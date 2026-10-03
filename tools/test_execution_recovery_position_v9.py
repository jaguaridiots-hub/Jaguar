import os
import tempfile
from datetime import datetime, timezone


def _now():
    return datetime.now(timezone.utc).isoformat()


def _intent():
    now = _now()

    return {
        "authorization_id": "AUTH-V9-POSITION",
        "trade_uuid": "TRADE-V9-POSITION",
        "client_order_id": "CLIENT-V9-POSITION",
        "symbol": "TEST",
        "timeframe": "15m",
        "mode": "LIVE",
        "decision": "LONG",
        "quantity": 100.0,
        "status": "AUTHORIZED",
        "created_at": now,
        "updated_at": now,
    }


def _fresh_db():
    fd, path = tempfile.mkstemp(
        prefix="jaguar-v9-position-",
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


def _seed_filled(db):
    db.insert_execution_intent(_intent())

    db.update_execution_intent(
        "AUTH-V9-POSITION",
        status="SUBMITTED",
    )

    db.update_execution_intent(
        "AUTH-V9-POSITION",
        status="FILLED",
    )


def _position():
    return {
        "authorization_id": "AUTH-V9-POSITION",
        "symbol": "TEST",
        "instrument_token": "TEST|001",
        "quantity": 100.0,
        "side": "BUY",
    }


def main():
    path, db, recovery = _fresh_db()

    try:
        db.init_db()
        _seed_filled(db)

        result = recovery.reconcile_execution_position(
            "AUTH-V9-POSITION",
            broker_position=_position(),
            instrument_token="TEST|001",
        )

        assert result["status"] == "PROTECTION_PENDING"

        parent = db.get_execution_intent(
            "AUTH-V9-POSITION"
        )

        assert parent["status"] == "PROTECTION_PENDING"

        print("V9_POSITION_EXACT_MATCH: PASS")

        # ------------------------------------------------------------
        # Quantity mismatch
        # ------------------------------------------------------------
        path, db, recovery = _fresh_db()
        db.init_db()
        _seed_filled(db)

        bad = _position()
        bad["quantity"] = 99.0

        result = recovery.reconcile_execution_position(
            "AUTH-V9-POSITION",
            broker_position=bad,
            instrument_token="TEST|001",
        )

        assert result["status"] == "HALTED"

        print("V9_POSITION_QUANTITY_MISMATCH_FAIL_CLOSED: PASS")

        # ------------------------------------------------------------
        # Instrument mismatch
        # ------------------------------------------------------------
        path, db, recovery = _fresh_db()
        db.init_db()
        _seed_filled(db)

        bad = _position()
        bad["instrument_token"] = "TEST|002"

        result = recovery.reconcile_execution_position(
            "AUTH-V9-POSITION",
            broker_position=bad,
            instrument_token="TEST|001",
        )

        assert result["status"] == "HALTED"

        print("V9_POSITION_INSTRUMENT_MISMATCH_FAIL_CLOSED: PASS")

        # ------------------------------------------------------------
        # Authorization mismatch
        # ------------------------------------------------------------
        path, db, recovery = _fresh_db()
        db.init_db()
        _seed_filled(db)

        bad = _position()
        bad["authorization_id"] = "AUTH-WRONG"

        result = recovery.reconcile_execution_position(
            "AUTH-V9-POSITION",
            broker_position=bad,
            instrument_token="TEST|001",
        )

        assert result["status"] == "HALTED"

        print("V9_POSITION_AUTHORIZATION_MISMATCH_FAIL_CLOSED: PASS")

        # ------------------------------------------------------------
        # Symbol mismatch
        # ------------------------------------------------------------
        path, db, recovery = _fresh_db()
        db.init_db()
        _seed_filled(db)

        bad = _position()
        bad["symbol"] = "OTHER"

        result = recovery.reconcile_execution_position(
            "AUTH-V9-POSITION",
            broker_position=bad,
            instrument_token="TEST|001",
        )

        assert result["status"] == "HALTED"

        print("V9_POSITION_SYMBOL_MISMATCH_FAIL_CLOSED: PASS")

        # ------------------------------------------------------------
        # Direction mismatch when broker explicitly supplies side
        # ------------------------------------------------------------
        path, db, recovery = _fresh_db()
        db.init_db()
        _seed_filled(db)

        bad = _position()
        bad["side"] = "SELL"

        result = recovery.reconcile_execution_position(
            "AUTH-V9-POSITION",
            broker_position=bad,
            instrument_token="TEST|001",
        )

        assert result["status"] == "HALTED"

        print("V9_POSITION_DIRECTION_FAIL_CLOSED: PASS")

        # ------------------------------------------------------------
        # Missing quantity
        # ------------------------------------------------------------
        path, db, recovery = _fresh_db()
        db.init_db()
        _seed_filled(db)

        bad = _position()
        bad.pop("quantity")

        result = recovery.reconcile_execution_position(
            "AUTH-V9-POSITION",
            broker_position=bad,
            instrument_token="TEST|001",
        )

        assert result["status"] == "HALTED"

        print("V9_POSITION_MISSING_QUANTITY_FAIL_CLOSED: PASS")

        # ------------------------------------------------------------
        # Recovery cannot bypass FILLED requirement
        # ------------------------------------------------------------
        path, db, recovery = _fresh_db()
        db.init_db()

        db.insert_execution_intent(_intent())

        result = recovery.reconcile_execution_position(
            "AUTH-V9-POSITION",
            broker_position=_position(),
            instrument_token="TEST|001",
        )

        assert result["status"] == "HALTED"

        print("V9_POSITION_STATE_GUARD_FAIL_CLOSED: PASS")

    finally:
        os.environ.pop("JAGUAR_DB_PATH", None)
        try:
            os.unlink(path)
        except FileNotFoundError:
            pass


if __name__ == "__main__":
    main()
