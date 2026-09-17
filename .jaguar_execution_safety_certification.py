from types import SimpleNamespace
from copy import deepcopy
import os
import subprocess
import sys

from intelligence.execution_gateway_v2 import ExecutionGatewayV2
from intelligence.execution_adapter import ExecutionAdapter

os.environ["JAGUAR_EXECUTION_MODE"] = "PAPER"


def valid_state():
    return SimpleNamespace(
        symbol="BTCUSDT",
        timeframe="15m",
        price=100.0,
        atr=2.0,
        spread=0.5,

        idm={
            "decision": "ENTER_LONG",
            "reasons": ["canonical test approval"],
            "missing": [],
        },

        market={
            "symbol": "BTCUSDT",
            "price": 100.0,
            "session": {"name": "OPEN"},
        },

        market_metadata={
            "source": "YAHOO",
            "synthetic": False,
            "live_data_valid": True,
            "execution_allowed": True,
            "instrument_token": "TEST-TOKEN",
        },

        structural_zone={
            "readiness": "CONFIRMED",
            "direction": "BULLISH",
            "zone_direction": "BULLISH",
            "location_quality": "INTERACTING",
        },

        trade={
            "status": "READY",
            "side": "LONG",
            "entry": 100.0,
            "stop_loss": 99.0,
            "targets": [101.0, 102.0, 103.0],
        },

        risk={
            "approved": True,
            "position_size": 10.0,
            "risk_percent": 1.0,
            "risk_amount": 10.0,
        },

        execution={},
    )


def invoke(state):
    result = ExecutionGatewayV2().process(state)
    execution = getattr(result, "execution", None)
    assert isinstance(execution, dict), "state.execution must be a dict"
    return execution


def assert_rejected(name, state, expected_status=None, expected_gate=None):
    execution = invoke(state)

    assert execution["ready"] is False, f"{name}: ready unexpectedly True"
    assert execution["approved"] is False, f"{name}: approved unexpectedly True"
    assert execution["authorization_id"] is None, (
        f"{name}: authorization_id unexpectedly populated"
    )

    if expected_status is not None:
        assert execution["status"] == expected_status, (
            f"{name}: expected status {expected_status!r}, "
            f"got {execution['status']!r}"
        )

    if expected_gate is not None:
        assert execution["gate"] == expected_gate, (
            f"{name}: expected gate {expected_gate!r}, "
            f"got {execution['gate']!r}"
        )

    print(
        f"{name:<34} PASS  "
        f"status={execution['status']} "
        f"gate={execution['gate']}"
    )


def assert_authorized(name, state):
    execution = invoke(state)

    assert execution["ready"] is True
    assert execution["approved"] is True
    assert execution["status"] == "EXECUTE"
    assert execution["gate"] == "AUTHORIZED"
    assert execution["authorization_id"]
    assert execution["client_order_id"]

    print(
        f"{name:<34} PASS  "
        f"status=EXECUTE gate=AUTHORIZED "
        f"auth={execution['authorization_id']}"
    )


def snapshot_source_state():
    tracked = subprocess.check_output(
        ["git", "status", "--short"],
        text=True,
    )
    head = subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        text=True,
    ).strip()
    return head, tracked


def main():
    before_head, before_status = snapshot_source_state()

    print("=== EXECUTION SAFETY CERTIFICATION v1 ===")
    print("HEAD:", before_head)
    print()

    # Baseline
    assert_authorized("VALID BASELINE", valid_state())

    # 0 — Market integrity
    cases = []

    s = valid_state()
    s.market_metadata["synthetic"] = True
    cases.append(("SYNTHETIC DATA", s, "BLOCKED", "MARKET_DATA"))

    s = valid_state()
    s.market_metadata["source"] = "offline_fallback"
    cases.append(("OFFLINE FALLBACK", s, "BLOCKED", "MARKET_DATA"))

    s = valid_state()
    s.market_metadata["live_data_valid"] = False
    cases.append(("INVALID LIVE DATA", s, "BLOCKED", "MARKET_DATA"))

    s = valid_state()
    s.market_metadata["execution_allowed"] = False
    cases.append(("EXECUTION DISALLOWED", s, "BLOCKED", "MARKET_DATA"))

    # 1 — IDM
    s = valid_state()
    s.idm["decision"] = "WAIT"
    cases.append(("IDM WAIT", s, "WAIT", "IDM"))

    s = valid_state()
    s.idm["decision"] = "AVOID"
    cases.append(("IDM AVOID", s, "BLOCKED", "IDM"))

    s = valid_state()
    s.idm["decision"] = "UNKNOWN"
    cases.append(("UNKNOWN IDM DECISION", s, "BLOCKED", "IDM"))

    # 2 — Structural execution readiness
    s = valid_state()
    s.structural_zone["readiness"] = "WAITING"
    cases.append(("STRUCTURE NOT CONFIRMED", s, "WAIT", "STRUCTURAL_ZONE"))

    s = valid_state()
    s.structural_zone["direction"] = "BEARISH"
    cases.append(("STRUCTURAL DIRECTION CONFLICT", s, "BLOCKED", "STRUCTURAL_DIRECTION"))

    s = valid_state()
    s.structural_zone["zone_direction"] = "BEARISH"
    cases.append(("ZONE DIRECTION CONFLICT", s, "BLOCKED", "ZONE_DIRECTION"))

    s = valid_state()
    s.structural_zone["location_quality"] = "NEAR"
    cases.append(("LOCATION NOT INTERACTING", s, "WAIT", "EXECUTION_LOCATION"))

    # 3 — Trade plan
    s = valid_state()
    s.trade["status"] = "WAIT"
    cases.append(("TRADE NOT READY", s, "BLOCKED", "TRADE_PLANNER"))

    s = valid_state()
    s.trade["entry"] = None
    cases.append(("MISSING ENTRY", s, "BLOCKED", "TRADE_PLANNER"))

    s = valid_state()
    s.trade["targets"] = []
    cases.append(("MISSING TARGETS", s, "BLOCKED", "TRADE_PLANNER"))

    s = valid_state()
    s.trade["entry"] = 0
    cases.append(("INVALID TRADE PRICE", s, "BLOCKED", "TRADE_PLANNER"))

    # 5 — Trade direction
    s = valid_state()
    s.trade["side"] = "SHORT"
    cases.append(("TRADE DIRECTION CONFLICT", s, "BLOCKED", "TRADE_DIRECTION"))

    # 6 — Geometry
    s = valid_state()
    s.trade["stop_loss"] = 101.0
    cases.append(("LONG STOP GEOMETRY", s, "BLOCKED", "TRADE_GEOMETRY"))

    s = valid_state()
    s.trade["targets"] = [99.0]
    cases.append(("LONG TARGET GEOMETRY", s, "BLOCKED", "TRADE_GEOMETRY"))

    # 7 — Risk
    s = valid_state()
    s.risk["approved"] = False
    cases.append(("RISK NOT APPROVED", s, "BLOCKED", "RISK_MANAGER"))

    s = valid_state()
    s.risk["position_size"] = 0
    cases.append(("ZERO POSITION SIZE", s, "BLOCKED", "POSITION_SIZE"))

    s = valid_state()
    s.risk["risk_percent"] = 0
    cases.append(("ZERO RISK PERCENT", s, "BLOCKED", "RISK_PERCENT"))

    # 8 — Freshness
    s = valid_state()
    s.market["price"] = 102.0
    cases.append(("STALE ENTRY", s, "WAIT", "ENTRY_FRESHNESS"))

    s = valid_state()
    s.atr = 0
    cases.append(("INVALID ATR", s, "BLOCKED", "ATR"))

    s = valid_state()
    s.price = 0
    s.market["price"] = 0
    cases.append(("INVALID MARKET PRICE", s, "BLOCKED", "MARKET_PRICE"))

    # 9 — Spread
    s = valid_state()
    s.spread = -1
    cases.append(("INVALID SPREAD", s, "BLOCKED", "SPREAD"))

    s = valid_state()
    s.spread = 5.01
    cases.append(("EXCESSIVE SPREAD", s, "BLOCKED", "SPREAD"))

    # 10 — Session
    s = valid_state()
    s.market["session"]["name"] = "CLOSED"
    cases.append(("CLOSED SESSION", s, "BLOCKED", "SESSION"))

    for name, state, status, gate in cases:
        assert_rejected(name, state, status, gate)

    # LIVE fail-closed
    print()
    print("=== LIVE FAIL-CLOSED ===")

    try:
        ExecutionAdapter("LIVE")
    except RuntimeError as exc:
        text = str(exc)
        assert "FAIL-CLOSED" in text
        print("LIVE EXPLICIT BROKER GUARD         PASS")
    else:
        raise AssertionError(
            "LIVE EXPLICIT BROKER GUARD did not reject"
        )

    # Source/worktree invariant
    after_head, after_status = snapshot_source_state()

    assert after_head == before_head, "HEAD changed during certification"
    assert after_status == before_status, (
        "Git worktree changed during certification\n"
        f"BEFORE:\n{before_status}\n"
        f"AFTER:\n{after_status}"
    )

    print()
    print("=== CERTIFICATION RESULT ===")
    print("EXECUTION SAFETY CERTIFICATION: PASS")
    print("NO PRODUCTION FILES MODIFIED")


if __name__ == "__main__":
    main()
