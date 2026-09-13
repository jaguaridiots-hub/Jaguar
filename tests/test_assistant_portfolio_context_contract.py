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

    canonical_portfolio = dict(portfolio)
    canonical_portfolio["broker"] = {
        "authority": "UPSTOX_SHORT_TERM_POSITIONS",
        "status": "UNAVAILABLE",
        "positions": [],
        "freshness": "UNKNOWN",
        "quantity_source": "UPSTOX_POSITION_API",
    }
    canonical_portfolio["account"] = {
        "authority": "UPSTOX_FUND_AND_MARGIN_V3",
        "status": "UNAVAILABLE",
        "available_to_trade": None,
        "cash_available_to_trade": None,
        "pledge_available_to_trade": None,
        "cash_margin_used": None,
        "pledge_margin_used": None,
        "unsettled_profit_today": None,
        "unsettled_profit_previous_days": None,
        "freshness": "UNKNOWN",
    }
    canonical_portfolio["reconciliation"] = {
        "status": "BROKER_UNAVAILABLE",
        "matches": [],
        "mismatches": [],
        "unmatched_broker_positions": [],
        "freshness": "UNKNOWN",
    }

    with patch(
        "core.canonical_portfolio_read_model.build_canonical_portfolio_snapshot",
        return_value=canonical_portfolio,
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
