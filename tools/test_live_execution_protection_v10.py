from copy import deepcopy

from intelligence.live_execution_protection import (
    LiveExecutionProtectionError,
    LiveExecutionProtectionService,
)


AUTH = "AUTH-D26"
CLIENT = "JQX-D26"
TOKEN = "NSE_EQ|D26"
SYMBOL = "SBIN"


class FakeDB:
    def __init__(self):
        self.intents = {}
        self.orders = {}
        self.protections = {}
        self.intent_updates = []

    def get_execution_intent(self, authorization_id):
        row = self.intents.get(authorization_id)
        return deepcopy(row) if row is not None else None

    def list_execution_orders(self, authorization_id):
        return [
            deepcopy(row)
            for row in self.orders.values()
            if row["authorization_id"] == authorization_id
        ]

    def update_execution_intent(self, authorization_id, *, status=None):
        row = self.intents[authorization_id]
        if status is not None:
            row["status"] = status
        self.intent_updates.append((authorization_id, status))

    def list_execution_protections(self, authorization_id):
        return [
            deepcopy(row)
            for row in self.protections.values()
            if row["authorization_id"] == authorization_id
        ]

    def insert_execution_protection(self, data):
        protection = deepcopy(data)
        protection_id = protection["protection_id"]
        if protection_id in self.protections:
            raise RuntimeError("duplicate protection insert")
        self.protections[protection_id] = protection

    def update_execution_protection(
        self,
        protection_id,
        *,
        status=None,
        broker_order_id=None,
        verified_qty=None,
        verified_price=None,
    ):
        row = self.protections[protection_id]

        if broker_order_id is not None:
            current = row.get("broker_order_id")
            if current is not None and current != broker_order_id:
                raise RuntimeError(
                    "immutable broker identity violation"
                )
            row["broker_order_id"] = broker_order_id

        if status is not None:
            row["status"] = status

        if verified_qty is not None:
            row["verified_qty"] = verified_qty

        if verified_price is not None:
            row["verified_price"] = verified_price


class FakeBroker:
    EXECUTION_MODE = "LIVE"

    def __init__(self):
        self.submit_calls = []
        self.history_calls = []
        self.submission_result = {"broker_order_id": "SL-D26-001"}
        self.submission_error = None
        self.history = []

    def submit_protection(self, intent, protection):
        self.submit_calls.append(
            (deepcopy(intent), deepcopy(protection))
        )

        if self.submission_error is not None:
            raise self.submission_error

        return deepcopy(self.submission_result)

    def get_order_history(
        self,
        *,
        broker_order_id=None,
        client_order_id=None,
    ):
        self.history_calls.append(
            {
                "broker_order_id": broker_order_id,
                "client_order_id": client_order_id,
            }
        )
        return deepcopy(self.history)


def live_intent(status="PROTECTION_PENDING"):
    return {
        "authorization_id": AUTH,
        "trade_uuid": "TRADE-D26",
        "client_order_id": CLIENT,
        "symbol": SYMBOL,
        "timeframe": "5m",
        "mode": "LIVE",
        "decision": "LONG",
        "quantity": 10.0,
        "requested_price": 100.0,
        "stop_loss": 95.0,
        "take_profit": 110.0,
        "run_id": "RUN-D26",
        "status": status,
    }


def build():
    db = FakeDB()
    broker = FakeBroker()
    db.intents[AUTH] = live_intent()
    db.orders["ORDER-D26"] = {
        "authorization_id": AUTH,
        "instrument_token": TOKEN,
    }

    service = LiveExecutionProtectionService(
        broker,
        database_module=db,
    )

    return db, broker, service


def main():
    # LIVE service must reject a PAPER broker.
    class PaperBroker:
        EXECUTION_MODE = "PAPER"

    db = FakeDB()
    db.intents[AUTH] = live_intent()

    try:
        LiveExecutionProtectionService(
            PaperBroker(),
            database_module=db,
        )
    except LiveExecutionProtectionError:
        print("D26_PAPER_BROKER_FAIL_CLOSED: PASS")
    else:
        raise AssertionError(
            "PAPER broker accepted by LIVE protection service"
        )

    # Durable protection creation must occur before broker submission.
    db, broker, service = build()

    result = service.ensure_protections(AUTH)

    assert result["status"] == "PENDING"
    assert len(result["created_protections"]) == 2
    assert len(db.protections) == 2
    assert broker.submit_calls == []

    for row in db.protections.values():
        assert row["status"] == "PENDING"
        assert row["broker_order_id"] is None

    print("D26_DURABLE_PROTECTION_CREATION: PASS")

    # First submission must call broker exactly once and persist identity.
    # Use a fresh service/database so this protection is genuinely new.
    db, broker, service = build()

    result = service.submit_new_protection(
        AUTH,
        "STOP_LOSS",
        0,
    )

    sl_id = f"{AUTH}:PROTECTION:SL"

    assert result["action"] == "IDENTIFIED"
    assert result["broker_order_id"] == "SL-D26-001"
    assert len(broker.submit_calls) == 1
    assert db.protections[sl_id]["broker_order_id"] == "SL-D26-001"
    assert db.protections[sl_id]["status"] == "PENDING"

    print("D26_SINGLE_PROTECTION_SUBMISSION: PASS")

    # Persisted identity must prevent another broker submission.
    before = len(broker.submit_calls)

    result = service.submit_pending_protection(
        AUTH,
        sl_id,
    )

    assert result["action"] == "IDENTITY_ALREADY_PERSISTED"
    assert len(broker.submit_calls) == before

    print("D26_DUPLICATE_SUBMISSION_PREVENTED: PASS")

    # Existing PENDING + no broker ID is ambiguous and must never resubmit.
    db, broker, service = build()
    service.ensure_protections(AUTH)

    tp_id = f"{AUTH}:PROTECTION:TP0"
    before = len(broker.submit_calls)

    try:
        service.submit_pending_protection(
            AUTH,
            tp_id,
        )
    except LiveExecutionProtectionError as exc:
        assert "recovery is required" in str(exc)
    else:
        raise AssertionError(
            "Ambiguous PENDING protection was resubmitted"
        )

    assert len(broker.submit_calls) == before

    print("D26_AMBIGUOUS_PENDING_NO_RESUBMIT: PASS")

    # Simulated lost submission response.
    db, broker, service = build()
    broker.submission_error = RuntimeError(
        "simulated lost response"
    )

    result = service.submit_new_protection(
        AUTH,
        "STOP_LOSS",
        0,
    )

    assert result["action"] == "RECOVERY_REQUIRED"
    assert result["status"] == "PENDING"
    assert len(broker.submit_calls) == 1
    assert db.protections[
        f"{AUTH}:PROTECTION:SL"
    ]["broker_order_id"] is None

    print("D26_LOST_RESPONSE_RECOVERY_REQUIRED: PASS")

    # Exactly one historical broker match recovers identity without resubmit.
    broker.submission_error = None
    broker.history = [
        {
            "order_id": "SL-D26-RECOVERED",
            "tag": f"{CLIENT}-SL",
            "instrument_token": TOKEN,
            "quantity": 10,
            "transaction_type": "SELL",
            "order_type": "SL-M",
            "trigger_price": 95.0,
            "price": 0.0,
            "status": "OPEN",
        }
    ]

    result = service.recover_pending_protection(
        AUTH,
        f"{AUTH}:PROTECTION:SL",
    )

    assert result["action"] == "RECOVERED_IDENTITY"
    assert result["broker_order_id"] == "SL-D26-RECOVERED"
    assert db.protections[
        f"{AUTH}:PROTECTION:SL"
    ]["broker_order_id"] == "SL-D26-RECOVERED"
    assert len(broker.submit_calls) == 1
    assert broker.history_calls[-1]["client_order_id"] == (
        f"{CLIENT}-SL"
    )

    print("D26_LOST_RESPONSE_RECOVERED_WITHOUT_RESUBMIT: PASS")

    # Zero history must halt protection and parent.
    db, broker, service = build()
    service.ensure_protections(AUTH)

    result = service.recover_pending_protection(
        AUTH,
        f"{AUTH}:PROTECTION:SL",
    )

    assert result["status"] == "HALTED"
    assert db.intents[AUTH]["status"] == "HALTED"
    assert db.protections[
        f"{AUTH}:PROTECTION:SL"
    ]["status"] == "HALTED"
    assert broker.submit_calls == []

    print("D26_ZERO_HISTORY_FAIL_CLOSED: PASS")

    # Multiple history records must halt, never choose arbitrarily.
    db, broker, service = build()
    service.ensure_protections(AUTH)

    broker.history = [
        {
            "order_id": "SL-D26-A",
            "tag": f"{CLIENT}-SL",
            "instrument_token": TOKEN,
            "quantity": 10,
            "transaction_type": "SELL",
            "order_type": "SL-M",
            "trigger_price": 95.0,
            "price": 0.0,
            "status": "OPEN",
        },
        {
            "order_id": "SL-D26-B",
            "tag": f"{CLIENT}-SL",
            "instrument_token": TOKEN,
            "quantity": 10,
            "transaction_type": "SELL",
            "order_type": "SL-M",
            "trigger_price": 95.0,
            "price": 0.0,
            "status": "OPEN",
        },
    ]

    result = service.recover_pending_protection(
        AUTH,
        f"{AUTH}:PROTECTION:SL",
    )

    assert result["status"] == "HALTED"
    assert db.intents[AUTH]["status"] == "HALTED"
    assert db.protections[
        f"{AUTH}:PROTECTION:SL"
    ]["status"] == "HALTED"

    print("D26_MULTIPLE_HISTORY_FAIL_CLOSED: PASS")

    # Direction mismatch must fail closed and must not persist identity.
    db, broker, service = build()
    service.ensure_protections(AUTH)

    broker.history = [
        {
            "order_id": "SL-D26-BAD-DIR",
            "tag": f"{CLIENT}-SL",
            "instrument_token": TOKEN,
            "quantity": 10,
            "transaction_type": "BUY",
            "order_type": "SL-M",
            "trigger_price": 95.0,
            "price": 0.0,
            "status": "OPEN",
        }
    ]

    try:
        service.recover_pending_protection(
            AUTH,
            f"{AUTH}:PROTECTION:SL",
        )
    except LiveExecutionProtectionError:
        assert db.protections[
            f"{AUTH}:PROTECTION:SL"
        ]["broker_order_id"] is None
        print("D26_DIRECTION_MISMATCH_FAIL_CLOSED: PASS")
    else:
        raise AssertionError(
            "Protection direction mismatch was accepted"
        )

    # Instrument mismatch must fail closed.
    db, broker, service = build()
    service.ensure_protections(AUTH)

    broker.history = [
        {
            "order_id": "SL-D26-BAD-TOKEN",
            "tag": f"{CLIENT}-SL",
            "instrument_token": "NSE_EQ|WRONG",
            "quantity": 10,
            "transaction_type": "SELL",
            "order_type": "SL-M",
            "trigger_price": 95.0,
            "price": 0.0,
            "status": "OPEN",
        }
    ]

    try:
        service.recover_pending_protection(
            AUTH,
            f"{AUTH}:PROTECTION:SL",
        )
    except LiveExecutionProtectionError:
        assert db.protections[
            f"{AUTH}:PROTECTION:SL"
        ]["broker_order_id"] is None
        print("D26_INSTRUMENT_MISMATCH_FAIL_CLOSED: PASS")
    else:
        raise AssertionError(
            "Protection instrument mismatch was accepted"
        )

    # Terminal protection must never submit.
    db, broker, service = build()
    service.ensure_protections(AUTH)

    sl_id = f"{AUTH}:PROTECTION:SL"
    db.protections[sl_id]["status"] = "VERIFIED"

    result = service.submit_pending_protection(
        AUTH,
        sl_id,
    )

    assert result["status"] == "VERIFIED"
    assert result["action"] == "UNCHANGED_TERMINAL"
    assert broker.submit_calls == []

    print("D26_TERMINAL_NO_SUBMISSION: PASS")

    # Non-finite intent quantity must fail closed.
    db, broker, service = build()
    db.intents[AUTH]["quantity"] = float("nan")

    try:
        service.ensure_protections(AUTH)
    except LiveExecutionProtectionError:
        print("D26_NONFINITE_QUANTITY_FAIL_CLOSED: PASS")
    else:
        raise AssertionError(
            "NaN protection quantity was accepted"
        )

    # Non-finite intent price must fail closed.
    db, broker, service = build()
    db.intents[AUTH]["stop_loss"] = float("inf")

    try:
        service.ensure_protections(AUTH)
    except LiveExecutionProtectionError:
        print("D26_NONFINITE_PRICE_FAIL_CLOSED: PASS")
    else:
        raise AssertionError(
            "Infinite protection price was accepted"
        )

    # Missing durable execution-order lineage must fail closed.
    db, broker, service = build()
    db.orders.clear()

    try:
        service.ensure_protections(AUTH)
    except LiveExecutionProtectionError:
        print("D26_MISSING_INSTRUMENT_LINEAGE_FAIL_CLOSED: PASS")
    else:
        raise AssertionError(
            "Protection service accepted missing durable instrument lineage"
        )

    # Conflicting durable execution-order tokens must fail closed.
    db, broker, service = build()
    db.orders["ORDER-D26-2"] = {
        "authorization_id": AUTH,
        "instrument_token": "NSE_EQ|CONFLICT",
    }

    try:
        service.ensure_protections(AUTH)
    except LiveExecutionProtectionError:
        print("D26_AMBIGUOUS_INSTRUMENT_LINEAGE_FAIL_CLOSED: PASS")
    else:
        raise AssertionError(
            "Protection service accepted conflicting durable instrument lineage"
        )

    # Missing required DB parent-update API must fail closed at construction.
    class IncompleteDB:
        get_execution_intent = db.get_execution_intent
        list_execution_protections = db.list_execution_protections
        insert_execution_protection = db.insert_execution_protection
        update_execution_protection = db.update_execution_protection

    try:
        LiveExecutionProtectionService(
            broker,
            database_module=IncompleteDB(),
        )
    except LiveExecutionProtectionError:
        print("D26_CONSTRUCTOR_DB_API_FAIL_CLOSED: PASS")
    else:
        raise AssertionError(
            "Protection service accepted incomplete database API"
        )

    # Invalid recovery lineage must fail closed explicitly.
    db, broker, service = build()
    service.ensure_protections(AUTH)

    sl_id = f"{AUTH}:PROTECTION:SL"
    db.protections[sl_id]["target_index"] = -1

    try:
        service.recover_pending_protection(
            AUTH,
            sl_id,
        )
    except LiveExecutionProtectionError:
        print("D26_INVALID_RECOVERY_LINEAGE_FAIL_CLOSED: PASS")
    else:
        raise AssertionError(
            "Invalid recovery target_index was accepted"
        )

    # The new service must remain unwired.
    from pathlib import Path

    main_text = Path("main.py").read_text()
    assert "LiveExecutionProtectionService(" not in main_text

    for path in Path("intelligence").glob("*.py"):
        if path.name == "live_execution_protection.py":
            continue
        text = path.read_text()
        assert "LiveExecutionProtectionService(" not in text

    print("D26_PRODUCTION_WIRING_ABSENT: PASS")
    print("\nD26_LIVE_EXECUTION_PROTECTION_V10: PASS")


if __name__ == "__main__":
    main()
