"""Isolated D2.3 live-execution activation barrier.

This module does not execute broker orders and is not wired into
main.py, ExecutionAdapter, execution_gateway_v2.py, or live authorization.

LIVE execution is allowed only when all required readiness conditions
are explicitly satisfied.
"""

from intelligence.live_execution_coordinator import (
    LiveExecutionCoordinator,
)


class LiveExecutionActivationError(RuntimeError):
    """Raised when the live activation barrier cannot be evaluated safely."""


class LiveExecutionActivationBarrier:
    """Fail-closed readiness barrier for future LIVE execution activation."""

    def __init__(self, *, database_module):
        if database_module is None:
            raise LiveExecutionActivationError(
                "FAIL-CLOSED: database module is required"
            )

        if not hasattr(
            database_module,
            "list_non_terminal_execution_submissions",
        ):
            raise LiveExecutionActivationError(
                "FAIL-CLOSED: recovery enumeration API is unavailable"
            )

        self.db = database_module

    @staticmethod
    def _blocked(gate, reason):
        return {
            "allowed": False,
            "status": "BLOCKED",
            "gate": gate,
            "reason": reason,
        }

    @staticmethod
    def _allowed():
        return {
            "allowed": True,
            "status": "ALLOW",
            "gate": "LIVE_ACTIVATION",
            "reason": "LIVE execution activation barrier satisfied",
        }

    def evaluate(
        self,
        execution,
        market_metadata,
        broker,
        *,
        activation_requested=False,
    ):
        if activation_requested is not True:
            return self._blocked(
                "ACTIVATION",
                "LIVE execution activation was not explicitly requested",
            )

        if not isinstance(execution, dict):
            return self._blocked(
                "EXECUTION",
                "Invalid execution contract",
            )

        if str(execution.get("mode", "")).strip().upper() != "LIVE":
            return self._blocked(
                "EXECUTION",
                "LIVE activation requires mode=LIVE",
            )

        if execution.get("ready") is not True:
            return self._blocked(
                "EXECUTION",
                "LIVE activation requires execution.ready=True",
            )

        if execution.get("approved") is not True:
            return self._blocked(
                "EXECUTION",
                "LIVE activation requires execution.approved=True",
            )

        if execution.get("status") != "EXECUTE":
            return self._blocked(
                "EXECUTION",
                "LIVE activation requires status=EXECUTE",
            )

        if execution.get("gate") != "AUTHORIZED":
            return self._blocked(
                "EXECUTION",
                "LIVE activation requires gate=AUTHORIZED",
            )

        required_execution_fields = (
            "authorization_id",
            "trade_uuid",
            "client_order_id",
            "symbol",
            "timeframe",
            "instrument_token",
            "decision",
        )

        for field in required_execution_fields:
            value = execution.get(field)
            if not isinstance(value, str) or not value.strip():
                return self._blocked(
                    "EXECUTION",
                    f"LIVE activation requires non-empty {field}",
                )

        if str(execution["decision"]).strip().upper() not in {
            "LONG",
            "SHORT",
        }:
            return self._blocked(
                "EXECUTION",
                "LIVE activation requires decision=LONG or SHORT",
            )

        raw_quantity = execution.get("quantity")

        if isinstance(raw_quantity, bool):
            return self._blocked(
                "EXECUTION",
                "LIVE activation requires a valid quantity",
            )

        try:
            quantity = float(raw_quantity)
        except (TypeError, ValueError):
            return self._blocked(
                "EXECUTION",
                "LIVE activation requires a valid quantity",
            )

        if (
            quantity != quantity
            or quantity in (float("inf"), float("-inf"))
            or quantity <= 0
            or not quantity.is_integer()
        ):
            return self._blocked(
                "EXECUTION",
                "LIVE activation requires a positive integer quantity",
            )

        if not isinstance(market_metadata, dict):
            return self._blocked(
                "MARKET_DATA",
                "Invalid market metadata",
            )

        if market_metadata.get("synthetic") is True:
            return self._blocked(
                "MARKET_DATA",
                "LIVE activation blocked for synthetic market data",
            )

        if market_metadata.get("live_data_valid") is not True:
            return self._blocked(
                "MARKET_DATA",
                "LIVE activation requires live_data_valid=True",
            )

        if market_metadata.get("execution_allowed") is not True:
            return self._blocked(
                "MARKET_DATA",
                "LIVE activation requires execution_allowed=True",
            )

        if broker is None:
            return self._blocked(
                "BROKER",
                "LIVE activation requires an explicit LIVE broker",
            )

        if str(
            getattr(broker, "EXECUTION_MODE", "")
        ).strip().upper() != "LIVE":
            return self._blocked(
                "BROKER",
                "LIVE activation requires broker EXECUTION_MODE=LIVE",
            )

        for method_name in (
            "submit_entry",
            "get_order_history",
        ):
            method = getattr(broker, method_name, None)
            if not callable(method):
                return self._blocked(
                    "BROKER",
                    f"LIVE broker lacks required method: {method_name}",
                )

        try:
            unresolved = self.db.list_non_terminal_execution_submissions()
        except Exception as exc:
            return self._blocked(
                "RECOVERY",
                f"Unable to inspect unresolved submissions: {type(exc).__name__}",
            )

        if unresolved is None:
            unresolved = []

        if not isinstance(unresolved, (list, tuple)):
            return self._blocked(
                "RECOVERY",
                "Unresolved submission enumeration returned a non-sequence",
            )

        if unresolved:
            return self._blocked(
                "RECOVERY",
                "LIVE activation blocked while non-terminal submissions exist",
            )

        return self._allowed()
