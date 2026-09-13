from types import SimpleNamespace
from unittest.mock import patch

from assistant.context import build_assistant_context


def test_assistant_receives_read_only_portfolio_state():
    state = SimpleNamespace(
        symbol="BTCUSDT",
        interval="15m",
        timeframe="15m",
        mode="SWING",
        run_id="TEST-RUN",
        master_decision={
            "decision": "WAIT",
            "approved": False,
            "score": 50,
            "confidence": 50,
            "reasons": [],
        },
        institutional_report={
            "enterprise": {
                "decision": "WAIT",
                "approved": False,
                "score": 50,
                "confidence": 50,
                "grade": "C",
                "risk": {},
                "execution": {
                    "mode": "PAPER",
                    "authorization_id": "MUST_NOT_LEAK",
                },
            }
        },
        idm={},
        market={
            "15m": {
                "candles": [
                    {
                        "close": 100.0,
                        "timestamp": "TEST",
                    }
                ]
            }
        },
        risk={},
        execution={
            "mode": "PAPER",
            "authorization_id": "MUST_NOT_LEAK",
        },
        structure={},
        mtf_indicators={},
    )

    portfolio = {
        "authority": "JAGUAR_EXECUTION_DATABASE",
        "status": "AVAILABLE",
        "positions": [],
        "realized_pnl": None,
        "unrealized_pnl": None,
        "equity": None,
        "available_cash": None,
        "freshness": "CURRENT",
        "quantity_source": "EXECUTION_ORDERS",
    }

    with patch(
        "core.portfolio_read_model.build_portfolio_snapshot",
        return_value=portfolio,
    ):
        context = build_assistant_context(
            state,
            {
                "enterprise": {
                    "decision": "WAIT",
                    "approved": False,
                }
            },
        )

    ui = context["ui_state"]

    assert context["read_only"] is True
    assert ui["portfolio"]["status"] == "AVAILABLE"
    assert ui["portfolio"]["positions"] == []
    assert ui["portfolio"]["quantity_source"] == "EXECUTION_ORDERS"
    assert "authorization_id" not in ui["portfolio"]
