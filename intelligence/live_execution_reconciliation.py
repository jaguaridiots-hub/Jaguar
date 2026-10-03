"""Isolated D2.5 LIVE execution reconciliation orchestration.

This module composes the sealed LIVE broker observation boundary with the
sealed V9 position/protection reconciliation primitives.

It performs no broker mutation, no order submission, no resubmission,
and no direct production wiring.
"""

from intelligence import execution_recovery
from intelligence.live_execution_coordinator import (
    LiveExecutionCoordinatorError,
)


class LiveExecutionReconciliationError(RuntimeError):
    """Raised when LIVE execution reconciliation cannot be completed safely."""


class LiveExecutionReconciliationService:
    """Ordered broker-observation and V9 reconciliation boundary."""

    def __init__(self, broker, *, database_module):
        if broker is None:
            raise LiveExecutionReconciliationError(
                "FAIL-CLOSED: explicit LIVE broker is required"
            )

        if str(
            getattr(broker, "EXECUTION_MODE", "")
        ).strip().upper() != "LIVE":
            raise LiveExecutionReconciliationError(
                "FAIL-CLOSED: reconciliation requires an explicit LIVE broker"
            )

        if not callable(getattr(broker, "observe_position", None)):
            raise LiveExecutionReconciliationError(
                "FAIL-CLOSED: LIVE broker lacks observe_position"
            )

        if not callable(getattr(broker, "observe_protection", None)):
            raise LiveExecutionReconciliationError(
                "FAIL-CLOSED: LIVE broker lacks observe_protection"
            )

        if database_module is None:
            raise LiveExecutionReconciliationError(
                "FAIL-CLOSED: database module is required"
            )

        for name in (
            "get_execution_intent",
            "list_execution_orders",
            "list_execution_protections",
            "update_execution_intent",
        ):
            if not callable(getattr(database_module, name, None)):
                raise LiveExecutionReconciliationError(
                    "FAIL-CLOSED: database API unavailable: "
                    f"{name}"
                )

        for name in (
            "reconcile_execution_position",
            "reconcile_execution_protection_group",
        ):
            if not callable(getattr(execution_recovery, name, None)):
                raise LiveExecutionReconciliationError(
                    "FAIL-CLOSED: V9 reconciliation API unavailable: "
                    f"{name}"
                )

        self.broker = broker
        self.db = database_module

    @staticmethod
    def _authorization_id(value):
        if not isinstance(value, str) or not value.strip():
            raise LiveExecutionReconciliationError(
                "FAIL-CLOSED: invalid authorization_id"
            )
        return value.strip()

    @staticmethod
    def _instrument_token(value):
        if not isinstance(value, str) or not value.strip():
            raise LiveExecutionReconciliationError(
                "FAIL-CLOSED: invalid instrument_token"
            )
        return value.strip()

    def _load_intent(self, authorization_id):
        row = self.db.get_execution_intent(authorization_id)

        if row is None:
            raise LiveExecutionReconciliationError(
                "FAIL-CLOSED: execution intent not found"
            )

        intent = dict(row)

        if (
            str(intent.get("authorization_id", "")).strip()
            != authorization_id
        ):
            raise LiveExecutionReconciliationError(
                "FAIL-CLOSED: execution intent authorization mismatch"
            )

        if str(intent.get("mode", "")).strip().upper() != "LIVE":
            raise LiveExecutionReconciliationError(
                "FAIL-CLOSED: reconciliation requires mode=LIVE"
            )

        return intent

    def _halt_intent(self, authorization_id, reason):
        try:
            self.db.update_execution_intent(
                authorization_id,
                status="HALTED",
            )
        except Exception as exc:
            raise LiveExecutionReconciliationError(
                "FAIL-CLOSED: unable to persist HALTED execution state"
            ) from exc

        return {
            "authorization_id": authorization_id,
            "status": "HALTED",
            "action": "HALTED",
            "reason": reason,
        }

    def _resolve_instrument_token(self, authorization_id):
        rows = self.db.list_execution_orders(authorization_id)

        if rows is None:
            rows = []

        if not isinstance(rows, (list, tuple)):
            raise LiveExecutionReconciliationError(
                "FAIL-CLOSED: execution order lineage must be a sequence"
            )

        if not rows:
            raise LiveExecutionReconciliationError(
                "FAIL-CLOSED: execution order lineage not found"
            )

        tokens = set()

        for row in rows:
            order = dict(row)
            token = order.get("instrument_token")

            if not isinstance(token, str) or not token.strip():
                raise LiveExecutionReconciliationError(
                    "FAIL-CLOSED: execution order lineage missing instrument_token"
                )

            tokens.add(token.strip())

        if len(tokens) != 1:
            raise LiveExecutionReconciliationError(
                "FAIL-CLOSED: execution order lineage has ambiguous instrument identity"
            )

        return next(iter(tokens))

    def reconcile_position(self, authorization_id):
        """Reconcile only the broker position and stop at PROTECTION_PENDING."""
        authorization_id = self._authorization_id(
            authorization_id
        )

        intent = self._load_intent(
            authorization_id
        )

        current_status = str(
            intent.get("status", "")
        ).strip().upper()

        if current_status in {
            "RECONCILED",
            "REJECTED",
            "CANCELLED",
            "HALTED",
        }:
            return {
                "authorization_id": authorization_id,
                "previous_status": current_status,
                "status": current_status,
                "action": "UNCHANGED_TERMINAL",
            }

        instrument_token = self._instrument_token(
            self._resolve_instrument_token(
                authorization_id
            )
        )

        try:
            broker_position = self.broker.observe_position(
                intent,
                instrument_token=instrument_token,
            )
        except Exception as exc:
            return self._halt_intent(
                authorization_id,
                f"Broker position observation failed: {type(exc).__name__}",
            )

        if broker_position is None:
            return self._halt_intent(
                authorization_id,
                "Broker position was not observed",
            )

        try:
            position_result = (
                execution_recovery.reconcile_execution_position(
                    authorization_id,
                    broker_position=broker_position,
                    instrument_token=instrument_token,
                )
            )
        except Exception as exc:
            raise LiveExecutionReconciliationError(
                "FAIL-CLOSED: V9 position reconciliation failed"
            ) from exc

        if not isinstance(position_result, dict):
            raise LiveExecutionReconciliationError(
                "FAIL-CLOSED: V9 position reconciliation returned invalid result"
            )

        position_status = str(
            position_result.get("status", "")
        ).strip().upper()

        if position_status in {
            "HALTED",
            "RECONCILED",
        }:
            return position_result

        if position_status != "PROTECTION_PENDING":
            raise LiveExecutionReconciliationError(
                "FAIL-CLOSED: unexpected V9 position reconciliation state"
            )

        return position_result

    def reconcile_execution(self, authorization_id):
        """Reconcile position first, then every durable protection."""
        authorization_id = self._authorization_id(
            authorization_id
        )

        intent = self._load_intent(
            authorization_id
        )

        current_status = str(
            intent.get("status", "")
        ).strip().upper()

        if current_status in {
            "RECONCILED",
            "REJECTED",
            "CANCELLED",
            "HALTED",
        }:
            return {
                "authorization_id": authorization_id,
                "previous_status": current_status,
                "status": current_status,
                "action": "UNCHANGED_TERMINAL",
            }

        instrument_token = self._instrument_token(
            self._resolve_instrument_token(
                authorization_id
            )
        )

        try:
            broker_position = self.broker.observe_position(
                intent,
                instrument_token=instrument_token,
            )
        except Exception as exc:
            return self._halt_intent(
                authorization_id,
                f"Broker position observation failed: {type(exc).__name__}",
            )

        if broker_position is None:
            return self._halt_intent(
                authorization_id,
                "Broker position was not observed",
            )

        try:
            position_result = (
                execution_recovery.reconcile_execution_position(
                    authorization_id,
                    broker_position=broker_position,
                    instrument_token=instrument_token,
                )
            )
        except Exception as exc:
            raise LiveExecutionReconciliationError(
                "FAIL-CLOSED: V9 position reconciliation failed"
            ) from exc

        if not isinstance(position_result, dict):
            raise LiveExecutionReconciliationError(
                "FAIL-CLOSED: V9 position reconciliation returned invalid result"
            )

        position_status = str(
            position_result.get("status", "")
        ).strip().upper()

        if position_status == "HALTED":
            return position_result

        if position_status != "PROTECTION_PENDING":
            if position_status == "RECONCILED":
                return position_result

            raise LiveExecutionReconciliationError(
                "FAIL-CLOSED: unexpected V9 position reconciliation state"
            )

        durable_protections = self.db.list_execution_protections(
            authorization_id
        )

        if durable_protections is None:
            durable_protections = []

        if not isinstance(durable_protections, (list, tuple)):
            raise LiveExecutionReconciliationError(
                "FAIL-CLOSED: durable protection lineage must be a sequence"
            )

        if not durable_protections:
            try:
                return execution_recovery.reconcile_execution_protection_group(
                    authorization_id,
                    broker_protections=[],
                    instrument_token=instrument_token,
                )
            except Exception as exc:
                raise LiveExecutionReconciliationError(
                    "FAIL-CLOSED: V9 protection reconciliation failed"
                ) from exc

        broker_protections = []

        for protection_row in durable_protections:
            protection = dict(protection_row)

            try:
                observed = self.broker.observe_protection(
                    intent,
                    protection,
                    instrument_token=instrument_token,
                )
            except Exception as exc:
                return self._halt_intent(
                    authorization_id,
                    "Broker protection observation failed: "
                    f"{type(exc).__name__}",
                )

            if observed is None:
                broker_protections.append(
                    {
                        "broker_order_id": protection.get(
                            "broker_order_id"
                        ),
                        "authorization_id": authorization_id,
                        "symbol": intent.get("symbol"),
                        "instrument_token": instrument_token,
                        "quantity": 0,
                        "status": "MISSING",
                        "order_type": "UNKNOWN",
                        "transaction_type": "UNKNOWN",
                    }
                )
            else:
                broker_protections.append(
                    dict(observed)
                )

        try:
            return execution_recovery.reconcile_execution_protection_group(
                authorization_id,
                broker_protections=broker_protections,
                instrument_token=instrument_token,
            )
        except Exception as exc:
            raise LiveExecutionReconciliationError(
                "FAIL-CLOSED: V9 protection reconciliation failed"
            ) from exc
