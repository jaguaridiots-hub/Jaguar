"""Isolated D2.6-P3 LIVE protection orchestration boundary."""

class LiveExecutionProtectionRuntimeError(RuntimeError):
    """Raised when P3 cannot proceed safely."""


class LiveExecutionProtectionRuntime:
    """Ordered composition boundary for LIVE protection readiness."""

    TERMINAL_PARENT_STATES = {
        "RECONCILED",
        "REJECTED",
        "CANCELLED",
        "HALTED",
    }

    TERMINAL_PROTECTION_STATES = {
        "VERIFIED",
        "FAILED",
        "HALTED",
    }

    def __init__(
        self,
        *,
        position_reconciliation,
        protection_service,
        database_module,
    ):
        if position_reconciliation is None:
            raise LiveExecutionProtectionRuntimeError(
                "FAIL-CLOSED: position reconciliation service is required"
            )

        if protection_service is None:
            raise LiveExecutionProtectionRuntimeError(
                "FAIL-CLOSED: protection service is required"
            )

        if database_module is None:
            raise LiveExecutionProtectionRuntimeError(
                "FAIL-CLOSED: database module is required"
            )

        if not callable(
            getattr(position_reconciliation, "reconcile_position", None)
        ):
            raise LiveExecutionProtectionRuntimeError(
                "FAIL-CLOSED: position reconciliation API unavailable"
            )

        if not callable(
            getattr(position_reconciliation, "reconcile_execution", None)
        ):
            raise LiveExecutionProtectionRuntimeError(
                "FAIL-CLOSED: final reconciliation API unavailable"
            )

        for name in (
            "ensure_protections",
            "submit_new_protection",
            "recover_pending_protection",
        ):
            if not callable(getattr(protection_service, name, None)):
                raise LiveExecutionProtectionRuntimeError(
                    "FAIL-CLOSED: protection API unavailable: "
                    f"{name}"
                )

        for name in (
            "get_execution_intent",
            "list_execution_protections",
        ):
            if not callable(getattr(database_module, name, None)):
                raise LiveExecutionProtectionRuntimeError(
                    "FAIL-CLOSED: database API unavailable: "
                    f"{name}"
                )

        self.position_reconciliation = position_reconciliation
        self.protection_service = protection_service
        self.db = database_module

    @staticmethod
    def _authorization_id(value):
        if not isinstance(value, str) or not value.strip():
            raise LiveExecutionProtectionRuntimeError(
                "FAIL-CLOSED: invalid authorization_id"
            )
        return value.strip()

    @staticmethod
    def _status(result):
        if not isinstance(result, dict):
            raise LiveExecutionProtectionRuntimeError(
                "FAIL-CLOSED: composed service returned invalid result"
            )

        status = str(
            result.get("status", "")
        ).strip().upper()

        if not status:
            raise LiveExecutionProtectionRuntimeError(
                "FAIL-CLOSED: composed service returned empty status"
            )

        return status

    def _load_intent(self, authorization_id):
        row = self.db.get_execution_intent(
            authorization_id
        )

        if row is None:
            raise LiveExecutionProtectionRuntimeError(
                "FAIL-CLOSED: execution intent not found"
            )

        intent = dict(row)

        if (
            str(
                intent.get("authorization_id", "")
            ).strip()
            != authorization_id
        ):
            raise LiveExecutionProtectionRuntimeError(
                "FAIL-CLOSED: execution intent authorization mismatch"
            )

        if (
            str(
                intent.get("mode", "")
            ).strip().upper()
            != "LIVE"
        ):
            raise LiveExecutionProtectionRuntimeError(
                "FAIL-CLOSED: P3 requires mode=LIVE"
            )

        return intent

    def _load_protections(self, authorization_id):
        rows = self.db.list_execution_protections(
            authorization_id
        )

        if rows is None:
            rows = []

        if not isinstance(rows, (list, tuple)):
            raise LiveExecutionProtectionRuntimeError(
                "FAIL-CLOSED: protection lineage must be a sequence"
            )

        protections = []

        for row in rows:
            protection = dict(row)

            protection_id = protection.get(
                "protection_id"
            )

            if (
                not isinstance(protection_id, str)
                or not protection_id.strip()
            ):
                raise LiveExecutionProtectionRuntimeError(
                    "FAIL-CLOSED: protection lineage missing protection_id"
                )

            protections.append(protection)

        return protections

    def _process_protections(self, authorization_id):
        ensure_result = self.protection_service.ensure_protections(
            authorization_id
        )

        if not isinstance(ensure_result, dict):
            raise LiveExecutionProtectionRuntimeError(
                "FAIL-CLOSED: protection ensure returned invalid result"
            )

        ensure_status = str(
            ensure_result.get("status", "")
        ).strip().upper()

        if ensure_status in self.TERMINAL_PARENT_STATES:
            return ensure_result

        created = ensure_result.get(
            "created_protections",
            [],
        )

        if not isinstance(created, list):
            raise LiveExecutionProtectionRuntimeError(
                "FAIL-CLOSED: created_protections must be a list"
            )

        created_set = set()

        for protection_id in created:
            if (
                not isinstance(protection_id, str)
                or not protection_id.strip()
            ):
                raise LiveExecutionProtectionRuntimeError(
                    "FAIL-CLOSED: invalid created protection identity"
                )
            created_set.add(protection_id)

        protections = self._load_protections(
            authorization_id
        )

        if not protections:
            raise LiveExecutionProtectionRuntimeError(
                "FAIL-CLOSED: protection ensure produced no durable protections"
            )

        results = []

        for protection in protections:
            protection_id = protection["protection_id"]

            status = str(
                protection.get("status", "")
            ).strip().upper()

            if status in self.TERMINAL_PROTECTION_STATES:
                results.append({
                    "authorization_id": authorization_id,
                    "protection_id": protection_id,
                    "status": status,
                    "action": "UNCHANGED_TERMINAL",
                })
                continue

            broker_order_id = protection.get(
                "broker_order_id"
            )

            if broker_order_id:
                results.append({
                    "authorization_id": authorization_id,
                    "protection_id": protection_id,
                    "broker_order_id": broker_order_id,
                    "status": status,
                    "action": "IDENTITY_ALREADY_PERSISTED",
                })
                continue

            if status != "PENDING":
                raise LiveExecutionProtectionRuntimeError(
                    "FAIL-CLOSED: unsupported protection state: "
                    f"{status}"
                )

            if protection_id in created_set:
                result = self.protection_service.submit_new_protection(
                    authorization_id,
                    protection["protection_type"],
                    protection.get("target_index", 0),
                )
            else:
                result = self.protection_service.recover_pending_protection(
                    authorization_id,
                    protection_id,
                )

            if not isinstance(result, dict):
                raise LiveExecutionProtectionRuntimeError(
                    "FAIL-CLOSED: protection operation returned invalid result"
                )

            results.append(result)

            result_status = self._status(result)

            if result_status in self.TERMINAL_PARENT_STATES:
                return {
                    "authorization_id": authorization_id,
                    "status": result_status,
                    "action": "PROTECTION_TERMINAL",
                    "protection_results": results,
                }

            if (
                str(
                    result.get("action", "")
                ).strip().upper()
                == "RECOVERY_REQUIRED"
            ):
                return {
                    "authorization_id": authorization_id,
                    "status": "PROTECTION_PENDING",
                    "action": "RECOVERY_REQUIRED",
                    "protection_results": results,
                }

        return {
            "authorization_id": authorization_id,
            "status": "PROTECTION_PENDING",
            "action": "PROTECTIONS_READY_FOR_RECONCILIATION",
            "protection_results": results,
        }

    def run(self, authorization_id):
        """Run position, protection, then final reconciliation."""
        authorization_id = self._authorization_id(
            authorization_id
        )

        intent = self._load_intent(
            authorization_id
        )

        current_status = str(
            intent.get("status", "")
        ).strip().upper()

        if current_status in self.TERMINAL_PARENT_STATES:
            return {
                "authorization_id": authorization_id,
                "previous_status": current_status,
                "status": current_status,
                "action": "UNCHANGED_TERMINAL",
            }

        position_result = (
            self.position_reconciliation.reconcile_position(
                authorization_id
            )
        )

        position_status = self._status(
            position_result
        )

        if position_status in self.TERMINAL_PARENT_STATES:
            return position_result

        if position_status != "PROTECTION_PENDING":
            raise LiveExecutionProtectionRuntimeError(
                "FAIL-CLOSED: position phase did not produce "
                "PROTECTION_PENDING"
            )

        protection_result = self._process_protections(
            authorization_id
        )

        protection_status = self._status(
            protection_result
        )

        if protection_status in self.TERMINAL_PARENT_STATES:
            return protection_result

        if (
            str(
                protection_result.get("action", "")
            ).strip().upper()
            == "RECOVERY_REQUIRED"
        ):
            return protection_result

        final_result = (
            self.position_reconciliation.reconcile_execution(
                authorization_id
            )
        )

        final_status = self._status(
            final_result
        )

        if final_status not in {
            "RECONCILED",
            "HALTED",
            "REJECTED",
            "CANCELLED",
        }:
            raise LiveExecutionProtectionRuntimeError(
                "FAIL-CLOSED: final reconciliation returned unexpected state"
            )

        return {
            "authorization_id": authorization_id,
            "status": final_status,
            "action": "FINAL_RECONCILIATION",
            "protection": protection_result,
            "final": final_result,
        }
