from types import SimpleNamespace

import intelligence.enterprise_adapter as enterprise_adapter
import intelligence.risk_manager_v2 as risk_manager
from intelligence.risk_manager_v2 import RiskManagerV2


def test_live_missing_account_returns_zero_capital(monkeypatch):
    monkeypatch.setattr(
        risk_manager.config,
        "get_execution_mode",
        lambda: "LIVE",
    )

    state = SimpleNamespace(account=None)

    assert RiskManagerV2._capital(state) == 0.0


def test_live_zero_available_to_trade_returns_zero_capital(monkeypatch):
    monkeypatch.setattr(
        risk_manager.config,
        "get_execution_mode",
        lambda: "LIVE",
    )

    state = SimpleNamespace(
        account={
            "status": "AVAILABLE",
            "freshness": "CURRENT",
            "available_to_trade": 0.0,
        }
    )

    assert RiskManagerV2._capital(state) == 0.0


def test_live_positive_current_available_to_trade_is_authoritative(monkeypatch):
    monkeypatch.setattr(
        risk_manager.config,
        "get_execution_mode",
        lambda: "LIVE",
    )

    state = SimpleNamespace(
        account={
            "status": "AVAILABLE",
            "freshness": "CURRENT",
            "available_to_trade": 5379.03,
        }
    )

    assert RiskManagerV2._capital(state) == 5379.03


def test_live_stale_account_returns_zero_capital(monkeypatch):
    monkeypatch.setattr(
        risk_manager.config,
        "get_execution_mode",
        lambda: "LIVE",
    )

    state = SimpleNamespace(
        account={
            "status": "AVAILABLE",
            "freshness": "STALE",
            "available_to_trade": 5379.03,
        }
    )

    assert RiskManagerV2._capital(state) == 0.0


def test_paper_preserves_default_capital(monkeypatch):
    monkeypatch.setattr(
        risk_manager.config,
        "get_execution_mode",
        lambda: "PAPER",
    )

    state = SimpleNamespace(account=None)

    assert RiskManagerV2._capital(state) == RiskManagerV2.DEFAULT_CAPITAL


def test_live_enterprise_adapter_populates_account(monkeypatch):
    expected = {
        "authority": "UPSTOX_FUNDS_V3",
        "status": "AVAILABLE",
        "freshness": "CURRENT",
        "available_to_trade": 5379.03,
        "cash_available_to_trade": 5379.03,
        "pledge_available_to_trade": None,
    }

    monkeypatch.setattr(
        enterprise_adapter.config,
        "get_execution_mode",
        lambda: "LIVE",
    )
    monkeypatch.setattr(
        enterprise_adapter,
        "build_account_snapshot",
        lambda: expected,
    )

    adapter = enterprise_adapter.EnterpriseAdapter()

    state = SimpleNamespace(
        metadata={},
        market={},
        symbol="BTCUSDT",
        timeframe="15m",
    )

    # Avoid running the full enterprise pipeline; this test targets the
    # account-authority injection boundary only.
    adapter.pipeline = SimpleNamespace(run=lambda value: value)

    result = adapter.process(state)

    assert result.account is expected
