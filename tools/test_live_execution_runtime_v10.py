"""D2.4 isolated LIVE execution runtime composition tests."""

from intelligence.live_execution_runtime import (
    LiveExecutionRuntimeBoundary,
    LiveExecutionRuntimeError,
)


class FakeBroker:
    EXECUTION_MODE = "LIVE"

    def __init__(self):
        self.submit_calls = 0

    def submit_entry(self, execution):
        self.submit_calls += 1
        raise AssertionError("D2.4 test boundary must not submit implicitly")

    def get_order_history(self, **kwargs):
        raise AssertionError("D2.4 test boundary must not query implicitly")


class FakeCoordinator:
    def __init__(self):
        self.recover_calls = []
        self.start_calls = []

    def recover_submission(self, authorization_id):
        self.recover_calls.append(authorization_id)
        return {"authorization_id": authorization_id, "status": "RECOVERED"}

    def start_submission(self, execution):
        self.start_calls.append(dict(execution))
        return {"status": "SUBMITTED"}


class FakeRecovery:
    def __init__(self):
        self.calls = 0

    def recover_all_non_terminal_submissions(self):
        self.calls += 1
        return [{"status": "RECOVERED"}]


class FakeBarrier:
    def __init__(self):
        self.calls = []

    def evaluate(
        self,
        execution,
        market_metadata,
        broker,
        *,
        activation_requested=False,
    ):
        self.calls.append(
            (
                dict(execution),
                dict(market_metadata),
                broker,
                activation_requested,
            )
        )
        return {
            "allowed": activation_requested is True,
            "status": "ALLOW" if activation_requested is True else "BLOCKED",
        }


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def build_runtime():
    broker = FakeBroker()
    coordinator = FakeCoordinator()
    recovery = FakeRecovery()
    barrier = FakeBarrier()

    runtime = LiveExecutionRuntimeBoundary(
        broker,
        coordinator=coordinator,
        recovery_service=recovery,
        activation_barrier=barrier,
    )

    return runtime, broker, coordinator, recovery, barrier


def test_constructor_rejects_missing_broker():
    try:
        LiveExecutionRuntimeBoundary(
            None,
            coordinator=FakeCoordinator(),
            recovery_service=FakeRecovery(),
            activation_barrier=FakeBarrier(),
        )
    except LiveExecutionRuntimeError:
        print("D24_MISSING_BROKER_FAIL_CLOSED: PASS")
        return

    raise AssertionError("Missing broker was accepted")


def test_constructor_rejects_paper_broker():
    class PaperBroker(FakeBroker):
        EXECUTION_MODE = "PAPER"

    try:
        LiveExecutionRuntimeBoundary(
            PaperBroker(),
            coordinator=FakeCoordinator(),
            recovery_service=FakeRecovery(),
            activation_barrier=FakeBarrier(),
        )
    except LiveExecutionRuntimeError:
        print("D24_PAPER_BROKER_FAIL_CLOSED: PASS")
        return

    raise AssertionError("Paper broker passed runtime boundary")


def test_constructor_rejects_incomplete_components():
    class BrokenCoordinator:
        pass

    try:
        LiveExecutionRuntimeBoundary(
            FakeBroker(),
            coordinator=BrokenCoordinator(),
            recovery_service=FakeRecovery(),
            activation_barrier=FakeBarrier(),
        )
    except LiveExecutionRuntimeError:
        print("D24_INCOMPLETE_COMPONENT_FAIL_CLOSED: PASS")
        return

    raise AssertionError("Incomplete coordinator passed runtime boundary")


def test_recovery_delegation():
    runtime, broker, coordinator, recovery, barrier = build_runtime()

    result = runtime.recover_unresolved()

    assert_true(
        recovery.calls == 1,
        "Recovery service was not called exactly once",
    )
    assert_true(
        result == [{"status": "RECOVERED"}],
        "Recovery result was not preserved",
    )
    assert_true(
        broker.submit_calls == 0,
        "Recovery caused an implicit broker submission",
    )

    print("D24_RECOVERY_DELEGATION: PASS")


def test_activation_delegation_and_broker_identity():
    runtime, broker, coordinator, recovery, barrier = build_runtime()

    execution = {
        "authorization_id": "AUTH-1",
        "mode": "LIVE",
    }
    market = {
        "live_data_valid": True,
        "execution_allowed": True,
    }

    result = runtime.evaluate_activation(
        execution,
        market,
        activation_requested=True,
    )

    assert_true(result["allowed"] is True, "Activation result was not preserved")
    assert_true(len(barrier.calls) == 1, "Activation barrier call count mismatch")
    assert_true(
        barrier.calls[0][2] is broker,
        "Runtime did not pass the explicit broker through unchanged",
    )
    assert_true(
        broker.submit_calls == 0,
        "Activation evaluation caused broker submission",
    )
    assert_true(
        not hasattr(runtime, "start_submission"),
        "Activation path exposes a submission bypass around D2.3",
    )

    print("D24_ACTIVATION_DELEGATION: PASS")


def test_no_submission_bypass():
    runtime, broker, coordinator, recovery, barrier = build_runtime()

    assert_true(
        not hasattr(runtime, "start_submission"),
        "D2.4 must not expose a submission bypass around D2.3",
    )

    assert_true(
        broker.submit_calls == 0,
        "Runtime construction caused broker submission",
    )

    print("D24_NO_SUBMISSION_BYPASS: PASS")


def test_no_implicit_network_transport():
    import intelligence.live_broker_adapter as live_adapter

    assert_true(
        callable(live_adapter.LiveBrokerAdapter),
        "LIVE broker adapter import failed",
    )

    runtime, broker, coordinator, recovery, barrier = build_runtime()

    assert_true(
        broker.submit_calls == 0,
        "Runtime instantiated or invoked network-facing broker behavior",
    )

    print("D24_NO_IMPLICIT_NETWORK_OR_BROKER_IO: PASS")


def main():
    test_constructor_rejects_missing_broker()
    test_constructor_rejects_paper_broker()
    test_constructor_rejects_incomplete_components()
    test_recovery_delegation()
    test_activation_delegation_and_broker_identity()
    test_no_submission_bypass()
    test_no_implicit_network_transport()
    print("D24_RUNTIME_BOUNDARY_CONTRACT: PASS")


if __name__ == "__main__":
    main()
