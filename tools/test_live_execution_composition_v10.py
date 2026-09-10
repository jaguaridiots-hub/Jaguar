"""D2.8-B1 LIVE execution composition contract tests."""

import os

import intelligence.live_execution_composition as composition


ENV_NAME = "JAGUAR_EXECUTION_MODE"


class FakeBroker:
    EXECUTION_MODE = "LIVE"

    def __init__(self):
        self.submit_calls = 0

    def submit_entry(self, execution):
        self.submit_calls += 1
        raise AssertionError(
            "Composition test must not submit to broker"
        )

    def get_order_history(self, **kwargs):
        raise AssertionError(
            "Composition test must not query broker"
        )


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def clear_mode():
    os.environ.pop(ENV_NAME, None)


def test_paper_mode_rejected():
    os.environ[ENV_NAME] = "PAPER"

    try:
        try:
            composition.build_live_execution_runtime(
                database_module=object(),
            )
        except composition.LiveExecutionCompositionError:
            pass
        else:
            raise AssertionError(
                "LIVE composition accepted PAPER mode"
            )
    finally:
        clear_mode()

    print("D28B1_PAPER_REJECTED: PASS")


def test_missing_mode_rejected_only_for_invalid_database_boundary():
    clear_mode()

    try:
        composition.build_live_execution_runtime(
            database_module=object(),
        )
    except composition.LiveExecutionCompositionError:
        pass
    else:
        raise AssertionError(
            "LIVE composition unexpectedly accepted default PAPER mode"
        )

    print("D28B1_DEFAULT_PAPER_REJECTED: PASS")


def test_invalid_mode_rejected():
    os.environ[ENV_NAME] = "LIVE_NOW"

    try:
        try:
            composition.build_live_execution_runtime(
                database_module=object(),
            )
        except composition.LiveExecutionCompositionError:
            pass
        else:
            raise AssertionError(
                "Invalid execution mode reached LIVE composition"
            )
    finally:
        clear_mode()

    print("D28B1_INVALID_MODE_REJECTED: PASS")


def test_live_composition_builds_with_injected_broker():
    os.environ[ENV_NAME] = "LIVE"

    original_broker = composition.LiveBrokerAdapter

    class FakeLiveBroker(FakeBroker):
        pass

    composition.LiveBrokerAdapter = FakeLiveBroker

    class FakeDB:
        def list_non_terminal_execution_submissions(self):
            return []

    try:
        runtime = composition.build_live_execution_runtime(
            database_module=FakeDB(),
        )

        assert_true(
            runtime is not None,
            "LIVE runtime was not returned",
        )

        assert_true(
            getattr(runtime.broker, "EXECUTION_MODE", None) == "LIVE",
            "Runtime broker is not LIVE",
        )

        assert_true(
            runtime.coordinator.broker is runtime.broker,
            "Coordinator does not use composed broker",
        )

        assert_true(
            runtime.recovery_service.coordinator is runtime.coordinator,
            "Recovery service does not use composed coordinator",
        )

        assert_true(
            runtime.activation_barrier.db is not None,
            "Activation barrier was not composed",
        )
    finally:
        composition.LiveBrokerAdapter = original_broker
        clear_mode()

    print("D28B1_LIVE_COMPOSITION: PASS")


def test_composition_does_not_submit():
    os.environ[ENV_NAME] = "LIVE"

    original_broker = composition.LiveBrokerAdapter

    class FakeLiveBroker(FakeBroker):
        pass

    composition.LiveBrokerAdapter = FakeLiveBroker

    class FakeDB:
        def list_non_terminal_execution_submissions(self):
            return []

    try:
        runtime = composition.build_live_execution_runtime(
            database_module=FakeDB(),
        )

        assert_true(
            runtime.broker.submit_calls == 0,
            "LIVE composition submitted during construction",
        )
    finally:
        composition.LiveBrokerAdapter = original_broker
        clear_mode()

    print("D28B1_NO_BROKER_SUBMISSION: PASS")


def test_missing_database_rejected():
    os.environ[ENV_NAME] = "LIVE"

    try:
        try:
            composition.build_live_execution_runtime(
                database_module=None,
            )
        except composition.LiveExecutionCompositionError:
            pass
        else:
            raise AssertionError(
                "Missing database module was accepted"
            )
    finally:
        clear_mode()

    print("D28B1_MISSING_DATABASE_FAIL_CLOSED: PASS")


def run():
    test_paper_mode_rejected()
    test_missing_mode_rejected_only_for_invalid_database_boundary()
    test_invalid_mode_rejected()
    test_live_composition_builds_with_injected_broker()
    test_composition_does_not_submit()
    test_missing_database_rejected()

    clear_mode()

    print("D28B1_COMPOSITION: PASS")


if __name__ == "__main__":
    run()
