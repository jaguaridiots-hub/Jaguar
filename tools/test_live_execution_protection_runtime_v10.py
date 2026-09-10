"""D2.6-P3 isolated LIVE protection orchestration tests."""

from copy import deepcopy

from intelligence.live_execution_protection_runtime import (
    LiveExecutionProtectionRuntime,
    LiveExecutionProtectionRuntimeError,
)


AUTH = "AUTH-P3"


class FakeDB:
    def __init__(self):
        self.intent = {
            "authorization_id": AUTH,
            "mode": "LIVE",
            "status": "FILLED",
        }
        self.protections = []

    def get_execution_intent(self, authorization_id):
        if authorization_id != AUTH:
            return None
        return deepcopy(self.intent)

    def list_execution_protections(self, authorization_id):
        if authorization_id != AUTH:
            return []
        return deepcopy(self.protections)


class FakePosition:
    def __init__(self):
        self.position_calls = 0
        self.final_calls = 0
        self.events = []
        self.position_result = {
            "authorization_id": AUTH,
            "status": "PROTECTION_PENDING",
        }
        self.final_result = {
            "authorization_id": AUTH,
            "status": "RECONCILED",
            "action": "RECONCILED",
        }

    def reconcile_position(self, authorization_id):
        self.position_calls += 1
        self.events.append("position")
        return deepcopy(self.position_result)

    def reconcile_execution(self, authorization_id):
        self.final_calls += 1
        self.events.append("final")
        return deepcopy(self.final_result)


class FakeProtection:
    def __init__(self, db):
        self.db = db
        self.ensure_calls = 0
        self.submit_calls = []
        self.recover_calls = []
        self.events = []
        self.submit_results = {}
        self.recover_results = {}
        self.created_ids = set()

    def ensure_protections(self, authorization_id):
        self.ensure_calls += 1
        self.events.append("ensure")

        existing_ids = {
            row["protection_id"]
            for row in self.db.protections
        }

        created_ids = []

        if "SL-P3" not in existing_ids:
            self.db.protections.append(
                {
                    "protection_id": "SL-P3",
                    "authorization_id": AUTH,
                    "protection_type": "STOP_LOSS",
                    "target_index": 0,
                    "broker_order_id": None,
                    "requested_qty": 10.0,
                    "requested_price": 95.0,
                    "status": "PENDING",
                }
            )
            created_ids.append("SL-P3")

        if "TP-P3" not in existing_ids:
            self.db.protections.append(
                {
                    "protection_id": "TP-P3",
                    "authorization_id": AUTH,
                    "protection_type": "TAKE_PROFIT",
                    "target_index": 0,
                    "broker_order_id": None,
                    "requested_qty": 10.0,
                    "requested_price": 110.0,
                    "status": "PENDING",
                }
            )
            created_ids.append("TP-P3")

        return {
            "authorization_id": AUTH,
            "status": "PENDING",
            "created_protections": created_ids,
        }

    def submit_new_protection(
        self,
        authorization_id,
        protection_type,
        target_index=0,
    ):
        self.submit_calls.append(
            (
                authorization_id,
                protection_type,
                target_index,
            )
        )
        self.events.append("submit")

        key = f"{protection_type}:{target_index}"

        result = deepcopy(
            self.submit_results.get(
                key,
                {
                    "authorization_id": AUTH,
                    "status": "PENDING",
                    "action": "IDENTIFIED",
                },
            )
        )

        if result.get("action") == "IDENTIFIED":
            for row in self.db.protections:
                if row["protection_type"] == protection_type:
                    row["broker_order_id"] = (
                        "BROKER-" + protection_type
                    )

        return result

    def recover_pending_protection(
        self,
        authorization_id,
        protection_id,
    ):
        self.recover_calls.append(
            (
                authorization_id,
                protection_id,
            )
        )
        self.events.append("recover")

        result = deepcopy(
            self.recover_results.get(
                protection_id,
                {
                    "authorization_id": AUTH,
                    "protection_id": protection_id,
                    "status": "PENDING",
                    "action": "RECOVERED_IDENTITY",
                    "broker_order_id": (
                        "RECOVERED-" + protection_id
                    ),
                },
            )
        )

        if result.get("action") == "RECOVERED_IDENTITY":
            for row in self.db.protections:
                if row["protection_id"] == protection_id:
                    row["broker_order_id"] = result[
                        "broker_order_id"
                    ]

        return result


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def build():
    db = FakeDB()
    position = FakePosition()
    protection = FakeProtection(db)

    shared_events = []
    position.events = shared_events
    protection.events = shared_events

    runtime = LiveExecutionProtectionRuntime(
        position_reconciliation=position,
        protection_service=protection,
        database_module=db,
    )

    return runtime, db, position, protection


def test_happy_path():
    runtime, db, position, protection = build()

    result = runtime.run(AUTH)

    assert_true(
        result["status"] == "RECONCILED",
        "P3 happy path did not reconcile",
    )
    assert_true(
        position.position_calls == 1,
        "Position phase was not called exactly once",
    )
    assert_true(
        position.final_calls == 1,
        "Final reconciliation was not called exactly once",
    )
    assert_true(
        protection.ensure_calls == 1,
        "Protection ensure was not called exactly once",
    )
    assert_true(
        len(protection.submit_calls) == 2,
        "Both protections were not submitted",
    )
    assert_true(
        protection.recover_calls == [],
        "Newly created protections entered recovery",
    )

    assert_true(
        position.events == [
            "position",
            "ensure",
            "submit",
            "submit",
            "final",
        ],
        "P3 component ordering was not preserved",
    )

    print("D26_P3_HAPPY_PATH: PASS")


def test_terminal_parent_noop():
    runtime, db, position, protection = build()
    db.intent["status"] = "RECONCILED"

    result = runtime.run(AUTH)

    assert_true(
        result["action"] == "UNCHANGED_TERMINAL",
        "Terminal parent was not a no-op",
    )
    assert_true(
        position.position_calls == 0,
        "Terminal parent caused position reconciliation",
    )
    assert_true(
        protection.ensure_calls == 0,
        "Terminal parent caused protection work",
    )

    print("D26_P3_TERMINAL_NOOP: PASS")


def test_position_halt():
    runtime, db, position, protection = build()

    position.position_result = {
        "authorization_id": AUTH,
        "status": "HALTED",
        "action": "HALTED",
    }

    result = runtime.run(AUTH)

    assert_true(
        result["status"] == "HALTED",
        "Position HALT was not propagated",
    )
    assert_true(
        protection.ensure_calls == 0,
        "Protection work occurred after position HALT",
    )
    assert_true(
        position.final_calls == 0,
        "Final reconciliation occurred after position HALT",
    )

    print("D26_P3_POSITION_HALT: PASS")


def test_mixed_lineage_uses_recovery_for_existing_pending():
    runtime, db, position, protection = build()

    db.protections = [
        {
            "protection_id": "SL-P3",
            "authorization_id": AUTH,
            "protection_type": "STOP_LOSS",
            "target_index": 0,
            "broker_order_id": None,
            "requested_qty": 10.0,
            "requested_price": 95.0,
            "status": "PENDING",
        }
    ]

    result = runtime.run(AUTH)

    assert_true(
        result["status"] == "RECONCILED",
        "Mixed protection lineage did not complete",
    )

    assert_true(
        protection.submit_calls == [
            (AUTH, "TAKE_PROFIT", 0),
        ],
        "New protection was not submitted exactly once",
    )

    assert_true(
        protection.recover_calls == [
            (AUTH, "SL-P3"),
        ],
        "Existing PENDING protection did not enter recovery",
    )

    print("D26_P3_MIXED_PENDING_RECOVERY: PASS")


def test_recovery_required_stops():
    runtime, db, position, protection = build()

    protection.submit_results["STOP_LOSS:0"] = {
        "authorization_id": AUTH,
        "status": "PENDING",
        "action": "RECOVERY_REQUIRED",
    }

    result = runtime.run(AUTH)

    assert_true(
        result["action"] == "RECOVERY_REQUIRED",
        "Recovery-required state was not surfaced",
    )
    assert_true(
        position.final_calls == 0,
        "Final reconciliation occurred before recovery",
    )

    print("D26_P3_RECOVERY_REQUIRED: PASS")


def test_invalid_position_result():
    runtime, db, position, protection = build()

    position.position_result = {
        "authorization_id": AUTH,
    }

    try:
        runtime.run(AUTH)
    except LiveExecutionProtectionRuntimeError:
        print("D26_P3_INVALID_POSITION_RESULT: PASS")
    else:
        raise AssertionError(
            "Invalid position result was accepted"
        )


def test_no_direct_broker_surface():
    runtime, db, position, protection = build()

    for name in (
        "submit_protection",
        "get_order_history",
        "observe_position",
        "observe_protection",
    ):
        assert_true(
            not hasattr(runtime, name),
            f"P3 exposes forbidden broker API: {name}",
        )

    print("D26_P3_NO_DIRECT_BROKER_API: PASS")


def test_constructor_fail_closed():
    db = FakeDB()
    position = FakePosition()
    protection = FakeProtection(db)

    class IncompletePosition:
        reconcile_position = position.reconcile_position

    try:
        LiveExecutionProtectionRuntime(
            position_reconciliation=IncompletePosition(),
            protection_service=protection,
            database_module=db,
        )
    except LiveExecutionProtectionRuntimeError:
        print("D26_P3_CONSTRUCTOR_FAIL_CLOSED: PASS")
    else:
        raise AssertionError(
            "P3 accepted incomplete position boundary"
        )


def test_production_wiring_absent():
    from pathlib import Path

    main_text = Path("main.py").read_text()

    assert "LiveExecutionProtectionRuntime(" not in main_text

    for path in Path("intelligence").glob("*.py"):
        if path.name == "live_execution_protection_runtime.py":
            continue

        text = path.read_text()

        assert (
            "LiveExecutionProtectionRuntime("
            not in text
        )

    print("D26_P3_PRODUCTION_WIRING_ABSENT: PASS")


def main():
    test_happy_path()
    test_terminal_parent_noop()
    test_position_halt()
    test_mixed_lineage_uses_recovery_for_existing_pending()
    test_recovery_required_stops()
    test_invalid_position_result()
    test_no_direct_broker_surface()
    test_constructor_fail_closed()
    test_production_wiring_absent()

    print(
        "\nD26_LIVE_EXECUTION_PROTECTION_RUNTIME_V10: PASS"
    )


if __name__ == "__main__":
    main()
