"""D2.3 isolated live-execution activation barrier tests."""

from intelligence.live_execution_activation import (
    LiveExecutionActivationBarrier,
)


class FakeDB:
    def __init__(self, rows=None, error=None):
        self.rows = rows
        self.error = error
        self.calls = 0

    def list_non_terminal_execution_submissions(self):
        self.calls += 1
        if self.error is not None:
            raise self.error
        return self.rows


class FakeBroker:
    EXECUTION_MODE = "LIVE"

    def __init__(self):
        self.submit_calls = 0
        self.history_calls = 0

    def submit_entry(self, execution):
        self.submit_calls += 1
        raise AssertionError("Barrier must never submit")

    def get_order_history(self, **kwargs):
        self.history_calls += 1
        raise AssertionError("Barrier must never query broker history")


def valid_execution():
    return {
        "mode": "LIVE",
        "ready": True,
        "approved": True,
        "status": "EXECUTE",
        "gate": "AUTHORIZED",
        "authorization_id": "AUTH-D23-001",
        "trade_uuid": "TRADE-D23-001",
        "client_order_id": "CLIENT-D23-001",
        "symbol": "BTCUSDT",
        "timeframe": "15m",
        "instrument_token": "TOKEN-D23-001",
        "decision": "LONG",
        "position_size": 1.0,
    }


def valid_market():
    return {
        "synthetic": False,
        "live_data_valid": True,
        "execution_allowed": True,
    }


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def test_activation_not_requested():
    barrier = LiveExecutionActivationBarrier(
        database_module=FakeDB([]),
    )

    result = barrier.evaluate(
        valid_execution(),
        valid_market(),
        FakeBroker(),
    )

    assert_true(result["allowed"] is False, "Unrequested LIVE activation was allowed")
    assert_true(result["gate"] == "ACTIVATION", "Wrong activation gate")
    print("D23_EXPLICIT_ACTIVATION_REQUIRED: PASS")


def test_happy_path():
    barrier = LiveExecutionActivationBarrier(
        database_module=FakeDB([]),
    )

    broker = FakeBroker()
    result = barrier.evaluate(
        valid_execution(),
        valid_market(),
        broker,
        activation_requested=True,
    )

    assert_true(result["allowed"] is True, "Valid LIVE activation was blocked")
    assert_true(result["status"] == "ALLOW", "Unexpected success status")
    assert_true(
        broker.submit_calls == 0 and broker.history_calls == 0,
        "Barrier performed broker I/O",
    )
    print("D23_HAPPY_PATH: PASS")


def test_unresolved_submission_blocks():
    barrier = LiveExecutionActivationBarrier(
        database_module=FakeDB(
            [{"authorization_id": "AUTH-D23-UNRESOLVED"}],
        ),
    )

    result = barrier.evaluate(
        valid_execution(),
        valid_market(),
        FakeBroker(),
        activation_requested=True,
    )

    assert_true(result["allowed"] is False, "Unresolved submission did not block")
    assert_true(result["gate"] == "RECOVERY", "Wrong recovery gate")
    print("D23_UNRESOLVED_RECOVERY_BLOCKS: PASS")


def test_market_integrity_blocks():
    barrier = LiveExecutionActivationBarrier(
        database_module=FakeDB([]),
    )

    market = valid_market()
    market["execution_allowed"] = False

    result = barrier.evaluate(
        valid_execution(),
        market,
        FakeBroker(),
        activation_requested=True,
    )

    assert_true(result["allowed"] is False, "Invalid market metadata did not block")
    assert_true(result["gate"] == "MARKET_DATA", "Wrong market-data gate")
    print("D23_MARKET_INTEGRITY_FAIL_CLOSED: PASS")


def test_broker_mode_blocks():
    class PaperBroker(FakeBroker):
        EXECUTION_MODE = "PAPER"

    barrier = LiveExecutionActivationBarrier(
        database_module=FakeDB([]),
    )

    result = barrier.evaluate(
        valid_execution(),
        valid_market(),
        PaperBroker(),
        activation_requested=True,
    )

    assert_true(result["allowed"] is False, "Paper broker passed LIVE barrier")
    assert_true(result["gate"] == "BROKER", "Wrong broker gate")
    print("D23_LIVE_BROKER_REQUIRED: PASS")


def test_invalid_execution_blocks():
    barrier = LiveExecutionActivationBarrier(
        database_module=FakeDB([]),
    )

    execution = valid_execution()
    execution["gate"] = "BLOCKED"

    result = barrier.evaluate(
        execution,
        valid_market(),
        FakeBroker(),
        activation_requested=True,
    )

    assert_true(result["allowed"] is False, "Invalid execution contract passed")
    assert_true(result["gate"] == "EXECUTION", "Wrong execution gate")
    print("D23_EXECUTION_AUTHORITY_FAIL_CLOSED: PASS")


def test_recovery_enumeration_failure_blocks():
    barrier = LiveExecutionActivationBarrier(
        database_module=FakeDB(
            error=RuntimeError("synthetic database failure"),
        ),
    )

    result = barrier.evaluate(
        valid_execution(),
        valid_market(),
        FakeBroker(),
        activation_requested=True,
    )

    assert_true(
        result["allowed"] is False,
        "Recovery enumeration failure did not block",
    )
    assert_true(result["gate"] == "RECOVERY", "Wrong recovery gate")
    print("D23_RECOVERY_INSPECTION_FAIL_CLOSED: PASS")


def run():
    tests = [
        test_activation_not_requested,
        test_happy_path,
        test_unresolved_submission_blocks,
        test_market_integrity_blocks,
        test_broker_mode_blocks,
        test_invalid_execution_blocks,
        test_recovery_enumeration_failure_blocks,
    ]

    for test in tests:
        test()


if __name__ == "__main__":
    run()
