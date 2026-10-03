from pathlib import Path

from core.alert_engine import AlertEngine


class FakeAdapter:
    def __init__(self):
        self.alerts = []

    def notify(self, alert):
        self.alerts.append(alert)
        return True


def test_healthy_portfolio_emits_nothing():
    adapter = FakeAdapter()
    engine = AlertEngine(adapter)

    result = engine.evaluate_portfolio(
        {
            "status": "AVAILABLE",
            "reconciliation": {"status": "NO_POSITIONS"},
        }
    )

    assert result is None
    assert adapter.alerts == []


def test_mismatch_emits_critical_alert():
    adapter = FakeAdapter()
    engine = AlertEngine(adapter)

    result = engine.evaluate_portfolio(
        {"status": "RECONCILIATION_MISMATCH"}
    )

    assert result is not None
    assert result.alert_type == "RECONCILIATION_MISMATCH"
    assert result.severity == "CRITICAL"
    assert result.execution_authority == "NONE"
    assert len(adapter.alerts) == 1


def test_same_failure_is_deduplicated():
    adapter = FakeAdapter()
    engine = AlertEngine(adapter, cooldown_seconds=300)

    portfolio = {"status": "BROKER_UNAVAILABLE"}

    assert engine.evaluate_portfolio(portfolio) is not None
    assert engine.evaluate_portfolio(portfolio) is None
    assert len(adapter.alerts) == 1


def test_recovery_is_emitted_after_failure():
    adapter = FakeAdapter()
    engine = AlertEngine(adapter, cooldown_seconds=300)

    engine.evaluate_portfolio({"status": "ACCOUNT_UNAVAILABLE"})

    recovery = engine.evaluate_portfolio(
        {
            "status": "AVAILABLE",
            "reconciliation": {"status": "NO_POSITIONS"},
        }
    )

    assert recovery is not None
    assert recovery.alert_type == "PORTFOLIO_RECOVERY"
    assert recovery.severity == "INFO"
    assert recovery.execution_authority == "NONE"


def test_unknown_state_fails_closed():
    adapter = FakeAdapter()
    engine = AlertEngine(adapter)

    result = engine.evaluate_portfolio(
        {
            "status": "UNKNOWN",
            "reconciliation": {"status": "UNKNOWN"},
        }
    )

    assert result is not None
    assert result.alert_type == "ALERT_OBSERVER_FAILURE"
    assert result.severity == "CRITICAL"
    assert result.execution_authority == "NONE"


def test_available_without_healthy_reconciliation_fails_closed():
    adapter = FakeAdapter()
    engine = AlertEngine(adapter)

    result = engine.evaluate_portfolio({"status": "AVAILABLE"})

    assert result is not None
    assert result.alert_type == "ALERT_OBSERVER_FAILURE"
    assert result.severity == "CRITICAL"
    assert result.execution_authority == "NONE"


def test_unreconcilable_state_is_critical():
    adapter = FakeAdapter()
    engine = AlertEngine(adapter)

    result = engine.evaluate_portfolio(
        {
            "status": "RECONCILIATION_MISMATCH",
            "reconciliation": {"status": "UNRECONCILABLE"},
        }
    )

    assert result is not None
    assert result.alert_type == "RECONCILIATION_MISMATCH"
    assert result.severity == "CRITICAL"


def test_alert_modules_have_no_execution_calls():
    forbidden = (
        "submit_entry",
        "place_order",
        "cancel_order",
        "execution_gateway",
        "execution_recovery",
        "update_execution_intent",
    )

    for name in (
        "core/alert_models.py",
        "core/alert_engine.py",
        "core/notification_adapter.py",
    ):
        text = Path(name).read_text()
        for token in forbidden:
            assert token not in text
