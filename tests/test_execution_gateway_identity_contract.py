"""
Jaguar Quant X — Execution Gateway Identity Contract

Proves that canonical market identity and timeframe reach the
authorized execution contract without being reconstructed.
"""

from core.market_state import MarketState
from intelligence.execution_gateway_v2 import ExecutionGatewayV2


def build_valid_state():
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

    state.idm = {
        "decision": "ENTER_LONG",
        "reasons": [],
    }

    state.structural_zone = {
        "readiness": "CONFIRMED",
        "direction": "BULLISH",
        "zone_direction": "BULLISH",
        "location_quality": "INTERACTING",
    }

    state.trade = {
        "entry": 100.0,
        "stop_loss": 99.0,
        "targets": [
            101.0,
            102.0,
            103.0,
        ],
        "side": "LONG",
        "status": "READY",
    }

    state.risk = {
        "approved": True,
        "position_size": 1.0,
        "risk_percent": 1.0,
        "risk_amount": 1.0,
    }

    state.atr = 2.0
    state.spread = 0.0

    return state


def main():
    gateway = ExecutionGatewayV2()

    state = build_valid_state()
    result = gateway.process(state)

    assert result is state

    execution = state.execution

    assert execution["ready"] is True
    assert execution["approved"] is True
    assert execution["status"] == "EXECUTE"
    assert execution["gate"] == "AUTHORIZED"

    assert execution["instrument_token"] == (
        "MCX_FO|GOLDM_TEST"
    )

    assert execution["timeframe"] == "15m"

    assert execution["symbol"] == "GOLDM"
    assert execution["decision"] == "ENTER_LONG"

    # No fabricated identity.
    missing_identity_state = build_valid_state()
    del missing_identity_state.market_metadata[
        "instrument_token"
    ]

    missing_result = gateway.process(
        missing_identity_state
    )

    assert missing_result.execution[
        "instrument_token"
    ] is None

    # No mode change is introduced by this patch.
    assert execution["broker"] == "Paper"

    print("EXECUTION_GATEWAY_IDENTITY_CONTRACT: PASS")
    print("Instrument-token propagation: PASS")
    print("Timeframe propagation: PASS")
    print("No identity fabrication: PASS")
    print("PAPER broker contract preserved: PASS")


if __name__ == "__main__":
    main()
