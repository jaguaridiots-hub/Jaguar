"""D2.7-A isolated execution-dispatch contract tests."""

from intelligence.live_execution_dispatch import (
    ExecutionDispatchRuntime,
    LiveExecutionDispatchError,
)


class FakeRuntime:
    def __init__(self):
        self.submit_calls = 0
        self.submit_args = []
        self.submit_result = {
            "mode": "LIVE",
            "status": "LIVE_OK",
        }

    def submit_live(
        self,
        execution,
        market_metadata,
        *,
        activation_requested=False,
    ):
        self.submit_calls += 1
        self.submit_args.append(
            (
                execution,
                market_metadata,
                activation_requested,
            )
        )
        return self.submit_result


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def build():
    calls = []
    runtime = FakeRuntime()

    def paper(execution):
        calls.append("paper")
        return {"mode": "PAPER", "status": "PAPER_OK"}

    dispatcher = ExecutionDispatchRuntime(
        paper_executor=paper,
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
    print("D27_PAPER_DELEGATION: PASS")


def test_live_delegation():
    dispatcher, runtime, calls = build()

    execution = {"mode": "LIVE"}
    market = {"live_data_valid": True}

    result = dispatcher.dispatch(
        execution,
        market,
        activation_requested=True,
    )

    assert_true(result["status"] == "LIVE_OK", "LIVE did not delegate")
    assert_true(calls == [], "PAPER executor ran for LIVE")
    assert_true(
        runtime.submit_calls == 1,
        "LIVE submission handoff was not called exactly once",
    )
    assert_true(
        runtime.submit_args == [
            (
                execution,
                market,
                True,
            )
        ],
        "LIVE handoff arguments were incorrect",
    )
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

    assert_true(calls == [], "LIVE executor was called before activation")
    print("D27_LIVE_WITHOUT_ACTIVATION_FAIL_CLOSED: PASS")


def test_live_runtime_submission_result_propagates():
    dispatcher, runtime, _ = build()

    runtime.submit_result = {
        "mode": "LIVE",
        "status": "SUBMITTED",
        "authorization_id": "AUTH",
    }

    result = dispatcher.dispatch(
        {"mode": "LIVE"},
        {"live_data_valid": True},
        activation_requested=True,
    )

    assert_true(
        result == runtime.submit_result,
        "LIVE runtime result was not propagated",
    )
    print("D27_LIVE_RESULT_PROPAGATION: PASS")


def test_live_runtime_requires_submission_api():
    class InvalidRuntime:
        pass

    try:
        ExecutionDispatchRuntime(
            paper_executor=lambda execution: None,
            live_runtime=InvalidRuntime(),
        )
    except LiveExecutionDispatchError:
        pass
    else:
        raise AssertionError(
            "Missing LIVE submission API did not fail closed"
        )

    print("D27_SUBMISSION_API_FAIL_CLOSED: PASS")


def test_legacy_live_executor_removed():
    try:
        ExecutionDispatchRuntime(
            paper_executor=lambda execution: None,
            live_executor=lambda execution: None,
            live_runtime=FakeRuntime(),
        )
    except TypeError:
        pass
    else:
        raise AssertionError(
            "Legacy live_executor injection is still accepted"
        )

    print("D27_LEGACY_LIVE_EXECUTOR_REMOVED: PASS")


def test_live_requires_runtime():
    try:
        ExecutionDispatchRuntime(
            paper_executor=lambda execution: None,
            live_runtime=None,
        )
    except LiveExecutionDispatchError:
        pass
    else:
        raise AssertionError("Missing LIVE runtime did not fail closed")

    print("D27_LIVE_WITHOUT_RUNTIME_FAIL_CLOSED: PASS")


def test_no_paper_fallback():
    dispatcher, runtime, calls = build()

    runtime.submit_result = {
        "mode": "LIVE",
        "status": "LIVE_BLOCKED",
    }

    result = dispatcher.dispatch(
        {"mode": "LIVE"},
        {},
        activation_requested=True,
    )

    assert_true(
        result["mode"] == "LIVE",
        "LIVE path changed mode",
    )
    assert_true(
        calls == [],
        "LIVE silently fell back to PAPER",
    )
    assert_true(
        runtime.submit_calls == 1,
        "LIVE runtime submission was not called",
    )
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


def test_no_runtime_gate_bypass():
    source = open(
        "intelligence/live_execution_dispatch.py",
        encoding="utf-8",
    ).read()

    forbidden = (
        "recover_unresolved",
        "evaluate_activation",
    )

    for token in forbidden:
        assert_true(
            token not in source,
            f"Runtime gate bypass remains: {token}",
        )

    assert_true(
        "submit_live" in source,
        "D2.4 submit_live() handoff missing",
    )

    print("D27_NO_RUNTIME_GATE_BYPASS: PASS")


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
            live_runtime=FakeRuntime(),
        )
    except LiveExecutionDispatchError:
        pass
    else:
        raise AssertionError("Invalid paper executor did not fail closed")

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
    test_live_requires_activation()
    test_live_runtime_submission_result_propagates()
    test_live_requires_runtime()
    test_live_runtime_requires_submission_api()
    test_legacy_live_executor_removed()
    test_no_paper_fallback()
    test_no_direct_broker_api()
    test_no_runtime_gate_bypass()
    test_production_wiring_absent()
    test_constructor_fail_closed()
    test_dispatch_contract()
    print()
    print("D27_EXECUTION_DISPATCH_V10: PASS")


if __name__ == "__main__":
    run()
