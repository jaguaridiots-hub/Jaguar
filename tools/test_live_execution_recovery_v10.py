"""D2.2 isolated live submission recovery orchestration tests."""

from intelligence.live_execution_recovery import (
    LiveExecutionRecoveryError,
    LiveExecutionRecoveryService,
)


class FakeDatabase:
    def __init__(self, rows):
        self.rows = rows
        self.calls = 0

    def list_non_terminal_execution_submissions(self):
        self.calls += 1
        return self.rows


class FakeCoordinator:
    def __init__(self, results=None):
        self.results = list(results or [])
        self.calls = []

    def recover_submission(self, authorization_id):
        self.calls.append(authorization_id)
        index = len(self.calls) - 1
        if index < len(self.results):
            return self.results[index]
        return {
            "authorization_id": authorization_id,
            "status": "HALTED",
        }


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def test_enumeration_and_order():
    db = FakeDatabase(
        [
            {
                "authorization_id": "AUTH-A",
                "status": "SUBMITTING",
            },
            {
                "authorization_id": "AUTH-B",
                "status": "IDENTIFIED",
            },
            {
                "authorization_id": "AUTH-C",
                "status": "SUBMITTING",
            },
        ]
    )
    coordinator = FakeCoordinator(
        [
            {"authorization_id": "AUTH-A", "status": "HALTED"},
            {"authorization_id": "AUTH-B", "status": "SUBMITTED"},
            {"authorization_id": "AUTH-C", "status": "HALTED"},
        ]
    )

    service = LiveExecutionRecoveryService(
        database_module=db,
        coordinator=coordinator,
    )

    results = service.recover_all_non_terminal_submissions()

    assert_true(
        db.calls == 1,
        "Database enumeration was not called exactly once",
    )
    assert_true(
        coordinator.calls == ["AUTH-A", "AUTH-B", "AUTH-C"],
        "Recovery delegation order was not preserved",
    )
    assert_true(
        results == coordinator.results,
        "Coordinator results were not preserved exactly",
    )


def test_empty_journal_is_noop():
    db = FakeDatabase([])
    coordinator = FakeCoordinator()

    service = LiveExecutionRecoveryService(
        database_module=db,
        coordinator=coordinator,
    )

    results = service.recover_all_non_terminal_submissions()

    assert_true(results == [], "Empty journal did not produce empty result")
    assert_true(
        coordinator.calls == [],
        "Coordinator was called for an empty journal",
    )


def test_none_journal_is_noop():
    db = FakeDatabase(None)
    coordinator = FakeCoordinator()

    service = LiveExecutionRecoveryService(
        database_module=db,
        coordinator=coordinator,
    )

    results = service.recover_all_non_terminal_submissions()

    assert_true(results == [], "None journal did not normalize to empty")
    assert_true(
        coordinator.calls == [],
        "Coordinator was called for a None journal",
    )


def test_invalid_authorization_fails_closed():
    db = FakeDatabase(
        [
            {
                "authorization_id": "",
                "status": "SUBMITTING",
            }
        ]
    )
    coordinator = FakeCoordinator()

    service = LiveExecutionRecoveryService(
        database_module=db,
        coordinator=coordinator,
    )

    try:
        service.recover_all_non_terminal_submissions()
    except LiveExecutionRecoveryError as exc:
        assert_true(
            "authorization_id" in str(exc),
            "Invalid authorization failure was not explicit",
        )
    else:
        raise AssertionError(
            "Invalid authorization did not fail closed"
        )

    assert_true(
        coordinator.calls == [],
        "Coordinator was invoked for invalid authorization",
    )


def test_invalid_enumeration_type_fails_closed():
    db = FakeDatabase({"authorization_id": "AUTH-A"})
    coordinator = FakeCoordinator()

    service = LiveExecutionRecoveryService(
        database_module=db,
        coordinator=coordinator,
    )

    try:
        service.recover_all_non_terminal_submissions()
    except LiveExecutionRecoveryError:
        pass
    else:
        raise AssertionError(
            "Invalid enumeration type did not fail closed"
        )

    assert_true(
        coordinator.calls == [],
        "Coordinator was invoked after invalid enumeration",
    )


def test_d2_2_constructor_requires_broker_without_injected_coordinator():
    db = FakeDatabase([])

    try:
        LiveExecutionRecoveryService(database_module=db)
    except LiveExecutionRecoveryError:
        pass
    else:
        raise AssertionError(
            "Missing broker/coordinator did not fail closed"
        )


def run():
    tests = [
        (
            "D22_ENUMERATION_AND_ORDER",
            test_enumeration_and_order,
        ),
        (
            "D22_EMPTY_JOURNAL_NOOP",
            test_empty_journal_is_noop,
        ),
        (
            "D22_NONE_JOURNAL_NOOP",
            test_none_journal_is_noop,
        ),
        (
            "D22_INVALID_AUTHORIZATION_FAIL_CLOSED",
            test_invalid_authorization_fails_closed,
        ),
        (
            "D22_INVALID_ENUMERATION_FAIL_CLOSED",
            test_invalid_enumeration_type_fails_closed,
        ),
        (
            "D22_CONSTRUCTOR_FAIL_CLOSED",
            test_d2_2_constructor_requires_broker_without_injected_coordinator,
        ),
    ]

    for name, test in tests:
        test()
        print(f"{name}: PASS")


if __name__ == "__main__":
    run()
