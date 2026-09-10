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

    state.execution_confirmation = {
        "decision": "ENTER_LONG",
        "score": 80,
        "probability": 90,
    }

    state.risk = {
        "position_size": 1.0,
        "risk_amount": 1.0,
        "risk_percent": 1.0,
    }

    state.price = 100.0

    return state


def authorize():
    state = build_state()

    gateway = ExecutionGatewayV2()

    result = gateway.process(state)

    return result.execution


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
