"""D2.7-A isolated execution-dispatch contract tests."""

from intelligence.live_execution_dispatch import (
    ExecutionDispatchRuntime,
    LiveExecutionDispatchError,
)


class FakeRuntime:
    def __init__(self):
        self.recovery_calls = 0
        self.activation_calls = 0
        self.recovery_result = []
        self.activation_result = {
            "allowed": True,
            "status": "ALLOW",
            "gate": "LIVE_ACTIVATION",
        }

    def recover_unresolved(self):
        self.recovery_calls += 1
        return self.recovery_result

    def evaluate_activation(
        self,
        execution,
        market_metadata,
        *,
        activation_requested=False,
    ):
        self.activation_calls += 1
        return self.activation_result


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def build():
    calls = []
    runtime = FakeRuntime()

    def paper(execution):
        calls.append("paper")
        return {"mode": "PAPER", "status": "PAPER_OK"}

    def live(execution):
        calls.append("live")
        return {"mode": "LIVE", "status": "LIVE_OK"}

    dispatcher = ExecutionDispatchRuntime(
        paper_executor=paper,
        live_executor=live,
        live_runtime=runtime,
    )

    return dispatcher, runtime, calls


def test_paper_delegation():
    dispatcher, runtime, calls = build()

    result = dispatcher.dispatch(
        {"mode": "PAPER"},
    )

    assert_true(result["status"] == "PAPER_OK", "PAPER did not delegate")
    assert_true(calls == ["paper"], "PAPER executor was not called")
    assert_true(runtime.recovery_calls == 0, "PAPER touched LIVE recovery")
    assert_true(runtime.activation_calls == 0, "PAPER touched LIVE activation")
    print("D27_PAPER_DELEGATION: PASS")


def test_live_delegation():
    dispatcher, runtime, calls = build()

    result = dispatcher.dispatch(
        {"mode": "LIVE"},
        {"live_data_valid": True},
        activation_requested=True,
    )

    assert_true(result["status"] == "LIVE_OK", "LIVE did not delegate")
    assert_true(calls == ["live"], "LIVE executor was not called")
    assert_true(runtime.recovery_calls == 1, "LIVE recovery was not called")
    assert_true(runtime.activation_calls == 1, "LIVE activation was not called")
    print("D27_LIVE_DELEGATION: PASS")


def test_missing_mode_fail_closed():
    dispatcher, _, _ = build()

    try:
        dispatcher.dispatch({})
    except LiveExecutionDispatchError:
        pass
    else:
        raise AssertionError("Missing mode did not fail closed")

    print("D27_MISSING_MODE_FAIL_CLOSED: PASS")


def test_invalid_mode_fail_closed():
    dispatcher, _, _ = build()

    try:
        dispatcher.dispatch({"mode": "OTHER"})
    except LiveExecutionDispatchError:
        pass
    else:
        raise AssertionError("Invalid mode did not fail closed")

    print("D27_INVALID_MODE_FAIL_CLOSED: PASS")


def test_live_requires_activation():
    dispatcher, runtime, calls = build()

    try:
        dispatcher.dispatch({"mode": "LIVE"})
    except LiveExecutionDispatchError:
        pass
    else:
        raise AssertionError("LIVE without activation did not fail closed")

    assert_true(runtime.recovery_calls == 0, "Recovery ran before activation")
    assert_true(runtime.activation_calls == 0, "Activation ran before explicit request")
    assert_true(calls == [], "LIVE executor was called before activation")
    print("D27_LIVE_WITHOUT_ACTIVATION_FAIL_CLOSED: PASS")


def test_live_requires_runtime():
    try:
        ExecutionDispatchRuntime(
            paper_executor=lambda execution: None,
            live_executor=lambda execution: None,
            live_runtime=None,
        )
    except LiveExecutionDispatchError:
        pass
    else:
        raise AssertionError("Missing LIVE runtime did not fail closed")

    print("D27_LIVE_WITHOUT_RUNTIME_FAIL_CLOSED: PASS")


def test_live_recovery_blocks():
    dispatcher, runtime, calls = build()
    runtime.recovery_result = [{"authorization_id": "AUTH"}]

    try:
        dispatcher.dispatch(
            {"mode": "LIVE"},
            {},
            activation_requested=True,
        )
    except LiveExecutionDispatchError:
        pass
    else:
        raise AssertionError("Unresolved recovery did not block LIVE")

    assert_true(runtime.activation_calls == 0, "Activation ran despite recovery")
    assert_true(calls == [], "LIVE executor ran despite recovery")
    print("D27_UNRESOLVED_RECOVERY_FAIL_CLOSED: PASS")


def test_live_activation_blocks():
    dispatcher, runtime, calls = build()
    runtime.activation_result = {
        "allowed": False,
        "status": "BLOCKED",
        "gate": "ACTIVATION",
    }

    try:
        dispatcher.dispatch(
            {"mode": "LIVE"},
            {},
            activation_requested=True,
        )
    except LiveExecutionDispatchError:
        pass
    else:
        raise AssertionError("Denied activation did not block LIVE")

    assert_true(runtime.recovery_calls == 1, "Recovery was not checked")
    assert_true(runtime.activation_calls == 1, "Activation was not checked")
    assert_true(calls == [], "LIVE executor ran after denied activation")
    print("D27_ACTIVATION_FAIL_CLOSED: PASS")


def test_no_paper_fallback():
    dispatcher, runtime, calls = build()
    runtime.activation_result = {
        "allowed": False,
        "status": "BLOCKED",
        "gate": "BROKER",
    }

    try:
        dispatcher.dispatch(
            {"mode": "LIVE"},
            {},
            activation_requested=True,
        )
    except LiveExecutionDispatchError:
        pass
    else:
        raise AssertionError("LIVE silently fell back to PAPER")

    assert_true(calls == [], "Fallback PAPER execution occurred")
    print("D27_NO_PAPER_FALLBACK: PASS")


def test_no_direct_broker_api():
    source = open(
        "intelligence/live_execution_dispatch.py",
        encoding="utf-8",
    ).read()

    forbidden = (
        "LiveBrokerAdapter",
        "submit_entry",
        "submit_protection",
        "place_order",
        "cancel_order",
    )

    for token in forbidden:
        assert_true(
            token not in source,
            f"Direct broker API reference found: {token}",
        )

    print("D27_NO_DIRECT_BROKER_API: PASS")


def test_production_wiring_absent():
    main_text = open("main.py", encoding="utf-8").read()

    assert_true(
        "ExecutionDispatchRuntime(" not in main_text,
        "D2.7 dispatcher is wired into main.py",
    )

    print("D27_PRODUCTION_WIRING_ABSENT: PASS")


def test_constructor_fail_closed():
    try:
        ExecutionDispatchRuntime(
            paper_executor=None,
            live_executor=lambda execution: None,
            live_runtime=FakeRuntime(),
        )
    except LiveExecutionDispatchError:
        pass
    else:
        raise AssertionError("Invalid paper executor did not fail closed")

    try:
        ExecutionDispatchRuntime(
            paper_executor=lambda execution: None,
            live_executor=None,
            live_runtime=FakeRuntime(),
        )
    except LiveExecutionDispatchError:
        pass
    else:
        raise AssertionError("Invalid LIVE executor did not fail closed")

    print("D27_CONSTRUCTOR_FAIL_CLOSED: PASS")


def test_dispatch_contract():
    dispatcher, _, _ = build()

    assert_true(
        callable(getattr(dispatcher, "dispatch", None)),
        "dispatch() API missing",
    )

    assert_true(
        dispatcher.PAPER == "PAPER",
        "PAPER mode contract changed",
    )

    assert_true(
        dispatcher.LIVE == "LIVE",
        "LIVE mode contract changed",
    )

    print("D27_DISPATCH_CONTRACT: PASS")


def run():
    test_paper_delegation()
    test_live_delegation()
    test_missing_mode_fail_closed()
    test_invalid_mode_fail_closed()
    test_live_requires_activation()
    test_live_requires_runtime()
    test_live_recovery_blocks()
    test_live_activation_blocks()
    test_no_paper_fallback()
    test_no_direct_broker_api()
    test_production_wiring_absent()
    test_constructor_fail_closed()
    test_dispatch_contract()
    print()
    print("D27_EXECUTION_DISPATCH_V10: PASS")


if __name__ == "__main__":
    run()
