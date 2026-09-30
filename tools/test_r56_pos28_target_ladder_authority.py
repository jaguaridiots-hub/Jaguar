"""
R56-POS-28 — Canonical execution target-ladder authority regression.

The canonical execution gateway must reject target ladders whose individual
targets are on the correct side of Entry but are not strictly monotonic.

Both BUY and SELL directions are covered, plus valid controls.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.market_state import MarketState
from intelligence.execution_gateway_v2 import ExecutionGatewayV2


def build_state(decision, targets):
    state = MarketState()

    state.symbol = "GOLDM"
    state.timeframe = "15m"

    state.market = {
        "symbol": "GOLDM",
        "price": 100.0,
        "session": {
            "name": "OPEN",
        },
    }

    state.market_metadata = {
        "source": "UPSTOX",
        "synthetic": False,
        "live_data_valid": True,
        "execution_allowed": True,
        "instrument_token": "MCX_FO|GOLDM_TEST",
    }

    bullish = decision == "ENTER_LONG"

    state.idm = {
        "decision": decision,
        "reasons": [],
    }

    state.structural_zone = {
        "readiness": "CONFIRMED",
        "direction": "BULLISH" if bullish else "BEARISH",
        "zone_direction": "BULLISH" if bullish else "BEARISH",
        "location_quality": "INTERACTING",
    }

    state.trade = {
        "status": "READY",
        "side": "LONG" if bullish else "SHORT",
        "decision": decision,
        "entry": 100.0,
        "stop_loss": 99.0 if bullish else 101.0,
        "targets": list(targets),
    }

    state.risk = {
        "approved": True,
        "reason": "Risk approved",
        "decision": decision,
        "entry": 100.0,
        "stop_loss": 99.0 if bullish else 101.0,
        "position_size": 1.0,
        "risk_percent": 1.0,
        "risk_amount": 1.0,
    }

    state.atr = 2.0
    state.spread = 0.0

    return state


def assert_blocked(execution, label):
    assert execution["ready"] is False, (
        f"{label}: expected ready=False, got {execution!r}"
    )
    assert execution["approved"] is False, (
        f"{label}: expected approved=False, got {execution!r}"
    )
    assert execution["status"] == "BLOCKED", (
        f"{label}: expected BLOCKED, got {execution!r}"
    )
    assert execution["gate"] == "TRADE_GEOMETRY", (
        f"{label}: expected TRADE_GEOMETRY, got {execution!r}"
    )


def assert_authorized(execution, label):
    assert execution["ready"] is True, (
        f"{label}: expected ready=True, got {execution!r}"
    )
    assert execution["approved"] is True, (
        f"{label}: expected approved=True, got {execution!r}"
    )
    assert execution["status"] == "EXECUTE", (
        f"{label}: expected EXECUTE, got {execution!r}"
    )
    assert execution["gate"] == "AUTHORIZED", (
        f"{label}: expected AUTHORIZED, got {execution!r}"
    )


def test_buy_inverted_target_ladder_rejected():
    execution = ExecutionGatewayV2().process(
        build_state(
            "ENTER_LONG",
            [110.0, 105.0, 115.0],
        )
    ).execution

    assert_blocked(
        execution,
        "BUY_INVERTED_TP_ORDER",
    )

    print(
        "R56_POS28_BUY_INVERTED_TP_ORDER_REJECTED: PASS"
    )


def test_sell_inverted_target_ladder_rejected():
    execution = ExecutionGatewayV2().process(
        build_state(
            "ENTER_SHORT",
            [90.0, 95.0, 80.0],
        )
    ).execution

    assert_blocked(
        execution,
        "SELL_INVERTED_TP_ORDER",
    )

    print(
        "R56_POS28_SELL_INVERTED_TP_ORDER_REJECTED: PASS"
    )


def test_buy_valid_target_ladder_authorized():
    execution = ExecutionGatewayV2().process(
        build_state(
            "ENTER_LONG",
            [110.0, 115.0, 120.0],
        )
    ).execution

    assert_authorized(
        execution,
        "BUY_VALID_TP_ORDER",
    )

    print(
        "R56_POS28_BUY_VALID_TP_ORDER_AUTHORIZED: PASS"
    )


def test_sell_valid_target_ladder_authorized():
    execution = ExecutionGatewayV2().process(
        build_state(
            "ENTER_SHORT",
            [90.0, 85.0, 80.0],
        )
    ).execution

    assert_authorized(
        execution,
        "SELL_VALID_TP_ORDER",
    )

    print(
        "R56_POS28_SELL_VALID_TP_ORDER_AUTHORIZED: PASS"
    )


def test_duplicate_target_ladder_rejected():
    execution = ExecutionGatewayV2().process(
        build_state(
            "ENTER_LONG",
            [110.0, 110.0, 120.0],
        )
    ).execution

    assert_blocked(
        execution,
        "BUY_DUPLICATE_TP_ORDER",
    )

    print(
        "R56_POS28_DUPLICATE_TP_ORDER_REJECTED: PASS"
    )


def test_two_target_ladder_rejected():
    execution = ExecutionGatewayV2().process(
        build_state(
            "ENTER_LONG",
            [110.0, 115.0],
        )
    ).execution

    assert_blocked(
        execution,
        "BUY_TWO_TARGETS",
    )

    print(
        "R56_POS28_TWO_TARGETS_REJECTED: PASS"
    )


def test_four_target_ladder_rejected():
    execution = ExecutionGatewayV2().process(
        build_state(
            "ENTER_LONG",
            [110.0, 115.0, 120.0, 125.0],
        )
    ).execution

    assert_blocked(
        execution,
        "BUY_FOUR_TARGETS",
    )

    print(
        "R56_POS28_FOUR_TARGETS_REJECTED: PASS"
    )


def test_nonfinite_target_rejected():
    execution = ExecutionGatewayV2().process(
        build_state(
            "ENTER_LONG",
            [110.0, float("nan"), 120.0],
        )
    ).execution

    assert execution["ready"] is False, (
        f"BUY_NAN_TARGET: expected ready=False, got {execution!r}"
    )
    assert execution["approved"] is False, (
        f"BUY_NAN_TARGET: expected approved=False, got {execution!r}"
    )
    assert execution["status"] == "BLOCKED", (
        f"BUY_NAN_TARGET: expected BLOCKED, got {execution!r}"
    )
    assert execution["gate"] == "TRADE_PLANNER", (
        f"BUY_NAN_TARGET: expected TRADE_PLANNER, got {execution!r}"
    )

    print(
        "R56_POS28_NAN_TARGET_REJECTED: PASS"
    )


def main():
    test_buy_inverted_target_ladder_rejected()
    test_sell_inverted_target_ladder_rejected()
    test_buy_valid_target_ladder_authorized()
    test_sell_valid_target_ladder_authorized()
    test_duplicate_target_ladder_rejected()
    test_two_target_ladder_rejected()
    test_four_target_ladder_rejected()
    test_nonfinite_target_rejected()


if __name__ == "__main__":
    main()
