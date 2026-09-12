from intelligence.live_execution_dispatch import (
    LiveExecutionDispatchError,
    normalize_live_execution,
)
from intelligence.live_execution_coordinator import (
    LiveExecutionCoordinator,
    LiveExecutionCoordinatorError,
)


def assert_equal(actual, expected, message):
    if actual != expected:
        raise AssertionError(
            f"{message}: expected={expected!r} actual={actual!r}"
        )


def assert_raises(exc_type, fn, message):
    try:
        fn()
    except exc_type:
        return
    raise AssertionError(message)


def gateway_execution():
    return {
        "mode": "LIVE",
        "ready": True,
        "approved": True,
        "status": "EXECUTE",
        "gate": "AUTHORIZED",
        "authorization_id": "AUTH-001",
        "trade_uuid": "TRADE-001",
        "client_order_id": "JGX-001",
        "symbol": "SBIN",
        "timeframe": "5m",
        "instrument_token": "NSE_EQ|TEST001",
        "decision": "ENTER_LONG",
        "position_size": 1,
    }


def test_gateway_to_canonical_long():
    source = gateway_execution()
    result = normalize_live_execution(source)

    assert_equal(result["decision"], "LONG", "LONG normalization failed")
    assert_equal(result["quantity"], 1, "quantity normalization failed")

    if "position_size" in result:
        raise AssertionError("position_size leaked into canonical contract")

    assert_equal(source["decision"], "ENTER_LONG", "source decision mutated")
    assert_equal(source["position_size"], 1, "source quantity mutated")

    print("GATEWAY_LONG_NORMALIZATION: PASS")


def test_gateway_to_canonical_short():
    source = gateway_execution()
    source["decision"] = "ENTER_SHORT"

    result = normalize_live_execution(source)

    assert_equal(result["decision"], "SHORT", "SHORT normalization failed")
    assert_equal(result["quantity"], 1, "SHORT quantity normalization failed")

    print("GATEWAY_SHORT_NORMALIZATION: PASS")


def test_invalid_quantities_fail_closed():
    for value in (
        0,
        -1,
        1.5,
        float("nan"),
        float("inf"),
        float("-inf"),
        True,
    ):
        source = gateway_execution()
        source["position_size"] = value

        assert_raises(
            LiveExecutionDispatchError,
            lambda source=source: normalize_live_execution(source),
            f"invalid quantity accepted: {value!r}",
        )

    print("INVALID_QUANTITY_FAIL_CLOSED: PASS")


def test_conflicting_quantities_fail_closed():
    source = gateway_execution()
    source["quantity"] = 2

    assert_raises(
        LiveExecutionDispatchError,
        lambda: normalize_live_execution(source),
        "conflicting quantity fields were accepted",
    )

    print("CONFLICTING_QUANTITY_FAIL_CLOSED: PASS")


def test_broker_translation_is_ephemeral():
    source = {
        "mode": "LIVE",
        "decision": "LONG",
        "quantity": 3,
    }

    result = LiveExecutionCoordinator._broker_execution(source)

    assert_equal(
        result["decision"],
        "ENTER_LONG",
        "broker LONG translation failed",
    )
    assert_equal(
        result["position_size"],
        3,
        "broker quantity translation failed",
    )

    if "quantity" in result:
        raise AssertionError("canonical quantity leaked into broker contract")

    assert_equal(source["decision"], "LONG", "canonical decision mutated")
    assert_equal(source["quantity"], 3, "canonical quantity mutated")

    source["decision"] = "SHORT"

    result = LiveExecutionCoordinator._broker_execution(source)

    assert_equal(
        result["decision"],
        "ENTER_SHORT",
        "broker SHORT translation failed",
    )
    assert_equal(
        result["position_size"],
        3,
        "broker SHORT quantity failed",
    )

    print("BROKER_TRANSLATION_EPHEMERAL: PASS")


def test_invalid_broker_direction_fail_closed():
    assert_raises(
        LiveExecutionCoordinatorError,
        lambda: LiveExecutionCoordinator._broker_execution(
            {
                "mode": "LIVE",
                "decision": "BAD",
                "quantity": 1,
            }
        ),
        "invalid broker direction accepted",
    )

    print("BROKER_DIRECTION_FAIL_CLOSED: PASS")


if __name__ == "__main__":
    test_gateway_to_canonical_long()
    test_gateway_to_canonical_short()
    test_invalid_quantities_fail_closed()
    test_conflicting_quantities_fail_closed()
    test_broker_translation_is_ephemeral()
    test_invalid_broker_direction_fail_closed()
    print("LIVE_CONTRACT_BOUNDARY: PASS")
