from __future__ import annotations

import time
from collections.abc import Mapping
from typing import Any

from core.alert_models import Alert
from core.notification_adapter import NotificationAdapter


_SEVERITY = {
    "BROKER_UNAVAILABLE": "CRITICAL",
    "ACCOUNT_UNAVAILABLE": "CRITICAL",
    "RECONCILIATION_MISMATCH": "CRITICAL",
    "BROKER_POSITION_WITHOUT_JAGUAR": "CRITICAL",
    "NO_BROKER_POSITION": "CRITICAL",
    "UNRECONCILABLE": "CRITICAL",
}


class AlertEngine:
    """Read-only operational alert evaluator."""

    def __init__(
        self,
        adapter: NotificationAdapter,
        cooldown_seconds: float = 300.0,
        clock=time.monotonic,
    ):
        if cooldown_seconds < 0:
            raise ValueError("cooldown_seconds must be >= 0")

        self.adapter = adapter
        self.cooldown_seconds = float(cooldown_seconds)
        self._clock = clock
        self._last_emitted: dict[str, float] = {}
        self._active: set[str] = set()

    @staticmethod
    def _status(portfolio: Mapping[str, Any]) -> str:
        status = portfolio.get("status")
        if isinstance(status, str) and status.strip():
            return status.strip().upper()

        reconciliation = portfolio.get("reconciliation")
        if isinstance(reconciliation, Mapping):
            status = reconciliation.get("status")
            if isinstance(status, str) and status.strip():
                return status.strip().upper()

        return "UNKNOWN"

    @staticmethod
    def _symbol(portfolio: Mapping[str, Any]) -> str | None:
        symbol = portfolio.get("symbol")
        if isinstance(symbol, str) and symbol.strip():
            return symbol.strip().upper()
        return None

    def _build_alert(
        self,
        portfolio: Mapping[str, Any],
        status: str,
    ) -> Alert | None:
        if status not in _SEVERITY:
            return None

        symbol = self._symbol(portfolio)
        suffix = f":{symbol}" if symbol else ""
        dedup_key = f"PORTFOLIO:{status}{suffix}"

        messages = {
            "BROKER_UNAVAILABLE": "Upstox broker position data is unavailable.",
            "ACCOUNT_UNAVAILABLE": "Upstox account/funds data is unavailable.",
            "RECONCILIATION_MISMATCH": (
                "Jaguar and broker portfolio quantities do not reconcile."
            ),
            "BROKER_POSITION_WITHOUT_JAGUAR": (
                "Broker reports a position with no matching Jaguar position."
            ),
            "NO_BROKER_POSITION": (
                "Jaguar reports a position but broker position data is absent."
            ),
            "UNRECONCILABLE": (
                "Jaguar and broker portfolio state could not be reconciled."
            ),
        }

        return Alert(
            alert_type=status,
            severity=_SEVERITY[status],
            message=messages[status],
            dedup_key=dedup_key,
            symbol=symbol,
        )

    @staticmethod
    def _healthy(portfolio: Mapping[str, Any]) -> bool:
        status = portfolio.get("status")
        reconciliation = portfolio.get("reconciliation")

        if status != "AVAILABLE" or not isinstance(reconciliation, Mapping):
            return False

        return reconciliation.get("status") in {
            "MATCH",
            "NO_POSITIONS",
        }

    def evaluate_portfolio(
        self,
        portfolio: Mapping[str, Any] | None,
    ) -> Alert | None:
        if not isinstance(portfolio, Mapping):
            return self._observer_failure()

        if self._healthy(portfolio):
            if self._active:
                self._active.clear()
                recovery = Alert(
                    alert_type="PORTFOLIO_RECOVERY",
                    severity="INFO",
                    message=(
                        "Jaguar portfolio monitoring returned "
                        "to a healthy state."
                    ),
                    dedup_key="PORTFOLIO:RECOVERY",
                    symbol=self._symbol(portfolio),
                )
                self.adapter.notify(recovery)
                return recovery
            return None

        status = self._status(portfolio)
        alert = self._build_alert(portfolio, status)

        if alert is None:
            return self._observer_failure()

        self._active.add(alert.dedup_key)

        now = self._clock()
        previous = self._last_emitted.get(alert.dedup_key)
        if previous is not None and now - previous < self.cooldown_seconds:
            return None

        self._last_emitted[alert.dedup_key] = now
        self.adapter.notify(alert)
        return alert

    def _observer_failure(self) -> Alert | None:
        alert = Alert(
            alert_type="ALERT_OBSERVER_FAILURE",
            severity="CRITICAL",
            message="Jaguar could not obtain the canonical portfolio state.",
            dedup_key="PORTFOLIO:OBSERVER_FAILURE",
        )

        now = self._clock()
        previous = self._last_emitted.get(alert.dedup_key)
        if previous is not None and now - previous < self.cooldown_seconds:
            return None

        self._last_emitted[alert.dedup_key] = now
        self._active.add(alert.dedup_key)
        self.adapter.notify(alert)
        return alert
