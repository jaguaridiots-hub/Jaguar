"""D2.8-A gateway execution-mode propagation contract tests."""

import os

from core.market_state import MarketState
from intelligence.execution_gateway_v2 import ExecutionGatewayV2


ENV_NAME = "JAGUAR_EXECUTION_MODE"


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def clear_mode():
    os.environ.pop(ENV_NAME, None)


def build_state():
    state = MarketState()
    state.symbol = "GOLDM"
    state.timeframe = "15m"

    state.market_metadata = {
        "source": "UPSTOX",
        "synthetic": False,
        "live_data_valid": True,
        "execution_allowed": True,
        "instrument_token": "MCX_FO|GOLDM_TEST",
    }

    state.idm = {
        "decision": "ENTER_LONG",
    }

    state.structural_zone = {
        "readiness": "CONFIRMED",
        "direction": "BULLISH",
        "zone_direction": "BULLISH",
        "location_quality": "INTERACTING",
    }

    state.trade = {
        "status": "READY",
        "entry": 100.0,
        "stop_loss": 99.0,
        "targets": [101.0],
        "side": "LONG",
    }

    state.risk = {
        "approved": True,
        "reason": "Risk approved",
        "position_size": 1.0,
        "risk_amount": 1.0,
        "risk_percent": 1.0,
    }

    state.price = 100.0
    state.atr = 2.0
    state.spread = 0.0
    state.market = {
        "price": 100.0,
        "symbol": "GOLDM",
        "session": {
            "name": "OPEN",
        },
    }

    return state


def authorize():
    state = build_state()

    gateway = ExecutionGatewayV2()

    result = gateway.process(state)
    execution = result.execution

    assert_true(
        execution["status"] == "EXECUTE",
        f"Fixture did not reach EXECUTE: {execution!r}",
    )
    assert_true(
        execution["gate"] == "AUTHORIZED",
        f"Fixture did not reach AUTHORIZED: {execution!r}",
    )

    return execution


def test_unset_mode_propagates_paper():
    clear_mode()

    execution = authorize()

    assert_true(
        execution["mode"] == "PAPER",
        f"Unset mode did not propagate PAPER: {execution.get('mode')!r}",
    )

    print("D28_GATEWAY_UNSET_PAPER: PASS")


def test_paper_mode_propagates():
    os.environ[ENV_NAME] = "PAPER"

    try:
        execution = authorize()

        assert_true(
            execution["mode"] == "PAPER",
            f"PAPER mode did not propagate: {execution.get('mode')!r}",
        )
    finally:
        clear_mode()

    print("D28_GATEWAY_PAPER: PASS")


def test_live_mode_propagates():
    os.environ[ENV_NAME] = "LIVE"

    try:
        execution = authorize()

        assert_true(
            execution["mode"] == "LIVE",
            f"LIVE mode did not propagate: {execution.get('mode')!r}",
        )

        assert_true(
            execution["broker"] == "Paper",
            "Legacy broker field changed unexpectedly",
        )
    finally:
        clear_mode()

    print("D28_GATEWAY_LIVE: PASS")


def test_invalid_mode_fails_closed():
    os.environ[ENV_NAME] = "LIVE_NOW"

    try:
        try:
            authorize()
        except RuntimeError as exc:
            assert_true(
                str(exc).startswith(
                    "FAIL-CLOSED: invalid execution mode:"
                ),
                "Gateway exposed the wrong invalid-mode failure",
            )
        else:
            raise AssertionError(
                "Gateway accepted an invalid execution mode"
            )
    finally:
        clear_mode()

    print("D28_GATEWAY_INVALID_MODE_FAIL_CLOSED: PASS")


def run():
    test_unset_mode_propagates_paper()
    test_paper_mode_propagates()
    test_live_mode_propagates()
    test_invalid_mode_fails_closed()

    clear_mode()

    print("D28_GATEWAY_EXECUTION_MODE: PASS")


if __name__ == "__main__":
    run()
