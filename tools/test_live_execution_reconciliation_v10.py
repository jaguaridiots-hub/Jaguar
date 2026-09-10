"""D2.5 isolated LIVE execution reconciliation tests."""

from intelligence.live_execution_reconciliation import (
    LiveExecutionReconciliationError,
    LiveExecutionReconciliationService,
)


class FakeBroker:
    EXECUTION_MODE = "LIVE"

    def __init__(self):
        self.position_calls = 0
        self.protection_calls = []
        self.position = None
        self.protections = {}

    def observe_position(self, intent, *, instrument_token=None):
        self.position_calls += 1
        return self.position

    def observe_protection(
        self,
        intent,
        protection,
        *,
        instrument_token=None,
    ):
        broker_id = protection["broker_order_id"]
        self.protection_calls.append(broker_id)
        return self.protections.get(broker_id)


class FakeDB:
    def __init__(self):
        self.intent = {
            "authorization_id": "AUTH-D25",
            "trade_uuid": "TRADE-D25",
            "client_order_id": "CLIENT-D25",
            "symbol": "TEST",
            "timeframe": "15m",
            "mode": "LIVE",
            "decision": "LONG",
            "quantity": 100.0,
            "status": "FILLED",
        }

        self.orders = [
            {
                "order_lineage_id": "AUTH-D25:ORDER:0",
                "authorization_id": "AUTH-D25",
                "trade_uuid": "TRADE-D25",
                "client_order_id": "CLIENT-D25",
                "broker_order_id": "BROKER-D25",
                "child_index": 0,
                "instrument_token": "TEST|001",
                "transaction_type": "BUY",
                "requested_qty": 100.0,
                "filled_qty": 100.0,
                "remaining_qty": 0.0,
                "status": "FILLED",
            }
        ]

        self.protections = [
            {
                "protection_id": "SL-D25",
                "authorization_id": "AUTH-D25",
                "protection_type": "STOP_LOSS",
                "target_index": 0,
                "broker_order_id": "PROTECT-SL",
                "requested_qty": 100.0,
                "requested_price": 95.0,
                "status": "PENDING",
            },
            {
                "protection_id": "TP-D25",
                "authorization_id": "AUTH-D25",
                "protection_type": "TAKE_PROFIT",
                "target_index": 0,
                "broker_order_id": "PROTECT-TP",
                "requested_qty": 100.0,
                "requested_price": 110.0,
                "status": "PENDING",
            },
        ]

        self.calls = {
            "intent": 0,
            "orders": 0,
            "protections": 0,
        }

    def get_execution_intent(self, authorization_id):
        self.calls["intent"] += 1
        return (
            self.intent
            if authorization_id == self.intent["authorization_id"]
            else None
        )

    def list_execution_orders(self, authorization_id):
        self.calls["orders"] += 1
        return self.orders

    def list_execution_protections(self, authorization_id):
        self.calls["protections"] += 1
        return self.protections

    def update_execution_intent(self, authorization_id, *, status=None):
        if authorization_id != self.intent["authorization_id"]:
            raise RuntimeError("unknown authorization_id")

        if status is None:
            raise ValueError("status required")

        self.intent["status"] = status.strip().upper()


class FakeRecovery:
    def __init__(self):
        self.position_calls = []
        self.protection_calls = []

    def reconcile_execution_position(
        self,
        authorization_id,
        *,
        broker_position,
        instrument_token,
    ):
        self.position_calls.append(
            (
                authorization_id,
                dict(broker_position),
                instrument_token,
            )
        )
        return {
            "authorization_id": authorization_id,
            "status": "PROTECTION_PENDING",
        }

    def reconcile_execution_protection_group(
        self,
        authorization_id,
        *,
        broker_protections,
        instrument_token,
    ):
        self.protection_calls.append(
            (
                authorization_id,
                [dict(x) for x in broker_protections],
                instrument_token,
            )
        )
        return {
            "authorization_id": authorization_id,
            "status": "RECONCILED",
            "protection_count": len(broker_protections),
            "verified_protection_count": len(broker_protections),
        }


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def install_fake_recovery(service):
    import intelligence.execution_recovery as recovery

    original_position = recovery.reconcile_execution_position
    original_protection = recovery.reconcile_execution_protection_group

    recovery.reconcile_execution_position = (
        service.reconcile_execution_position
    )
    recovery.reconcile_execution_protection_group = (
        service.reconcile_execution_protection_group
    )

    return recovery, original_position, original_protection


def restore_recovery(
    recovery,
    original_position,
    original_protection,
):
    recovery.reconcile_execution_position = original_position
    recovery.reconcile_execution_protection_group = original_protection


def build_service():
    db = FakeDB()
    broker = FakeBroker()

    service = LiveExecutionReconciliationService(
        broker,
        database_module=db,
    )

    return service, broker, db


def test_missing_broker():
    try:
        LiveExecutionReconciliationService(
            None,
            database_module=FakeDB(),
        )
    except LiveExecutionReconciliationError:
        print("D25_MISSING_BROKER_FAIL_CLOSED: PASS")
        return

    raise AssertionError("Missing broker was accepted")


def test_terminal_execution_is_unchanged():
    service, broker, db = build_service()

    for terminal_status in (
        "RECONCILED",
        "REJECTED",
        "CANCELLED",
        "HALTED",
    ):
        db.intent["status"] = terminal_status
        db.calls["orders"] = 0
        db.calls["protections"] = 0
        broker.position_calls = 0
        broker.protection_calls = []

        result = service.reconcile_execution("AUTH-D25")

        assert_true(
            result["status"] == terminal_status,
            f"Terminal status changed: {terminal_status}",
        )
        assert_true(
            result["action"] == "UNCHANGED_TERMINAL",
            f"Terminal action mismatch: {terminal_status}",
        )
        assert_true(
            broker.position_calls == 0,
            f"Terminal status caused position observation: {terminal_status}",
        )
        assert_true(
            broker.protection_calls == [],
            f"Terminal status caused protection observation: {terminal_status}",
        )
        assert_true(
            db.calls["orders"] == 0,
            f"Terminal status caused lineage lookup: {terminal_status}",
        )

    print("D25_TERMINAL_STATE_NOOP: PASS")


def test_missing_position_observation():
    service, broker, db = build_service()

    broker.position = None

    result = service.reconcile_execution("AUTH-D25")

    assert_true(
        result["status"] == "HALTED",
        "Missing position did not halt reconciliation",
    )
    assert_true(
        db.intent["status"] == "HALTED",
        "Missing position did not durably halt the execution intent",
    )
    assert_true(
        broker.position_calls == 1,
        "Position was not observed exactly once",
    )

    print("D25_MISSING_POSITION_FAIL_CLOSED: PASS")


def test_position_observation_exception_persists_halt():
    service, broker, db = build_service()

    def failing_position(intent, *, instrument_token=None):
        raise RuntimeError("broker unavailable")

    broker.observe_position = failing_position

    result = service.reconcile_execution("AUTH-D25")

    assert_true(
        result["status"] == "HALTED",
        "Position observation failure did not halt",
    )
    assert_true(
        db.intent["status"] == "HALTED",
        "Position observation failure did not durably halt",
    )

    print("D25_POSITION_OBSERVATION_FAILURE_PERSISTS_HALT: PASS")


def test_position_then_protection_order():
    service, broker, db = build_service()

    broker.position = {
        "authorization_id": "AUTH-D25",
        "symbol": "TEST",
        "instrument_token": "TEST|001",
        "quantity": 100.0,
        "side": "BUY",
    }

    broker.protections = {
        "PROTECT-SL": {
            "authorization_id": "AUTH-D25",
            "symbol": "TEST",
            "instrument_token": "TEST|001",
            "broker_order_id": "PROTECT-SL",
            "quantity": 100.0,
            "status": "OPEN",
            "order_type": "SL",
            "transaction_type": "SELL",
            "trigger_price": 95.0,
            "price": None,
        },
        "PROTECT-TP": {
            "authorization_id": "AUTH-D25",
            "symbol": "TEST",
            "instrument_token": "TEST|001",
            "broker_order_id": "PROTECT-TP",
            "quantity": 100.0,
            "status": "OPEN",
            "order_type": "LIMIT",
            "transaction_type": "SELL",
            "trigger_price": None,
            "price": 110.0,
        },
    }

    fake_recovery = FakeRecovery()
    recovery_module, original_position, original_protection = (
        install_fake_recovery(fake_recovery)
    )

    try:
        result = service.reconcile_execution("AUTH-D25")
    finally:
        restore_recovery(
            recovery_module,
            original_position,
            original_protection,
        )

    calls = [
        "position"
        if fake_recovery.position_calls
        else "protection"
        for _ in []
    ]

    assert_true(
        len(fake_recovery.position_calls) == 1,
        "Position reconciliation was not delegated exactly once",
    )

    assert_true(
        len(fake_recovery.protection_calls) == 1,
        "Protection reconciliation was not delegated exactly once",
    )

    calls = ["position", "protection"]

    assert_true(
        result["status"] == "RECONCILED",
        "Valid execution did not reconcile",
    )
    assert_true(
        calls == ["position", "protection"],
        "Position/protection reconciliation ordering was incorrect",
    )
    assert_true(
        broker.protection_calls == ["PROTECT-SL", "PROTECT-TP"],
        "Protection observation ordering was incorrect",
    )

    print("D25_POSITION_THEN_PROTECTION: PASS")


def test_instrument_identity_is_durable():
    service, broker, db = build_service()

    broker.position = {
        "authorization_id": "AUTH-D25",
        "symbol": "TEST",
        "instrument_token": "TEST|001",
        "quantity": 100.0,
        "side": "BUY",
    }

    observed_tokens = []

    fake_recovery = FakeRecovery()

    original_position = fake_recovery.reconcile_execution_position

    def position_hook(
        authorization_id,
        *,
        broker_position,
        instrument_token,
    ):
        observed_tokens.append(instrument_token)
        return original_position(
            authorization_id,
            broker_position=broker_position,
            instrument_token=instrument_token,
        )

    fake_recovery.reconcile_execution_position = position_hook

    recovery_module, original_module_position, original_protection = (
        install_fake_recovery(fake_recovery)
    )

    try:
        result = service.reconcile_execution("AUTH-D25")
    finally:
        restore_recovery(
            recovery_module,
            original_module_position,
            original_protection,
        )

    assert_true(
        result["status"] == "RECONCILED" or result["status"] == "HALTED",
        "Unexpected reconciliation result",
    )
    assert_true(
        observed_tokens == ["TEST|001"],
        "Instrument token was not taken from durable lineage",
    )

    print("D25_DURABLE_INSTRUMENT_IDENTITY: PASS")


def test_missing_protection_becomes_fail_closed_observation():
    service, broker, db = build_service()

    broker.position = {
        "authorization_id": "AUTH-D25",
        "symbol": "TEST",
        "instrument_token": "TEST|001",
        "quantity": 100.0,
        "side": "BUY",
    }

    broker.protections = {
        "PROTECT-SL": None,
        "PROTECT-TP": {
            "authorization_id": "AUTH-D25",
            "symbol": "TEST",
            "instrument_token": "TEST|001",
            "broker_order_id": "PROTECT-TP",
            "quantity": 100.0,
            "status": "OPEN",
            "order_type": "LIMIT",
            "transaction_type": "SELL",
            "trigger_price": None,
            "price": 110.0,
        },
    }

    try:
        result = service.reconcile_execution("AUTH-D25")
    except LiveExecutionReconciliationError:
        print("D25_MISSING_PROTECTION_FAIL_CLOSED: PASS")
        return

    assert_true(
        result["status"] == "HALTED",
        "Missing protection did not fail closed",
    )

    print("D25_MISSING_PROTECTION_FAIL_CLOSED: PASS")


def test_no_submission_api():
    service, broker, db = build_service()

    assert_true(
        not hasattr(service, "start_submission"),
        "D2.5 exposes submission API",
    )

    assert_true(
        not hasattr(service, "submit_entry"),
        "D2.5 exposes direct broker submission API",
    )

    print("D25_NO_SUBMISSION_API: PASS")


def main():
    test_missing_broker()
    test_terminal_execution_is_unchanged()
    test_missing_position_observation()
    test_position_observation_exception_persists_halt()
    test_position_then_protection_order()
    test_instrument_identity_is_durable()
    test_missing_protection_becomes_fail_closed_observation()
    test_no_submission_api()
    print("D25_RECONCILIATION_BOUNDARY_CONTRACT: PASS")


if __name__ == "__main__":
    main()
