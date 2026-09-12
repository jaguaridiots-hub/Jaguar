"""
Jaguar Quant X
Isolated LIVE Execution Coordinator

V9-D.2.1 isolated orchestration boundary.

This module is NOT wired into main.py, ExecutionAdapter, or the gateway.
LIVE execution remains disabled elsewhere.

The coordinator guarantees:
- LIVE-only broker binding
- authorization validation
- durable SUBMITTING journal before broker I/O
- no blind broker resubmission after ambiguous outcomes
- recovery through client_order_id/tag
- exactly one matching broker history record
- durable broker-order lineage before downstream reconciliation
- single broker entry order in this phase
"""

from datetime import datetime, timezone

from research import database as db


class LiveExecutionCoordinatorError(RuntimeError):
    """Raised when the isolated LIVE coordinator fails closed."""


class LiveExecutionCoordinator:
    EXECUTION_MODE = "LIVE"

    JOURNAL_SUBMITTING = "SUBMITTING"
    JOURNAL_IDENTIFIED = "IDENTIFIED"
    JOURNAL_LINEAGE_PERSISTED = "LINEAGE_PERSISTED"
    JOURNAL_HALTED = "HALTED"

    PARENT_AUTHORIZED = "AUTHORIZED"
    PARENT_SUBMITTING = "SUBMITTING"
    PARENT_SUBMITTED = "SUBMITTED"
    PARENT_HALTED = "HALTED"

    def __init__(self, broker, *, database_module=db):
        mode = str(
            getattr(broker, "EXECUTION_MODE", "")
        ).strip().upper()

        if mode != self.EXECUTION_MODE:
            raise LiveExecutionCoordinatorError(
                "FAIL-CLOSED: coordinator requires an explicit LIVE broker"
            )

        for name in ("submit_entry", "get_order_history"):
            if not callable(getattr(broker, name, None)):
                raise LiveExecutionCoordinatorError(
                    "FAIL-CLOSED: LIVE broker lacks required coordinator API: "
                    f"{name}"
                )

        self.broker = broker
        self.db = database_module

    @staticmethod
    def _now():
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _string(value, field):
        if not isinstance(value, str) or not value.strip():
            raise LiveExecutionCoordinatorError(
                f"FAIL-CLOSED: invalid {field}"
            )
        return value.strip()

    @staticmethod
    def _quantity(value):
        if isinstance(value, bool):
            raise LiveExecutionCoordinatorError(
                "FAIL-CLOSED: invalid quantity"
            )
        try:
            value = float(value)
        except (TypeError, ValueError) as exc:
            raise LiveExecutionCoordinatorError(
                "FAIL-CLOSED: invalid quantity"
            ) from exc

        if (
            value != value
            or value in (float("inf"), float("-inf"))
            or value <= 0
        ):
            raise LiveExecutionCoordinatorError(
                "FAIL-CLOSED: invalid quantity"
            )

        return value

    @staticmethod
    def _side(decision):
        decision = str(decision).strip().upper()

        if decision == "LONG":
            return "BUY"
        if decision == "SHORT":
            return "SELL"

        raise LiveExecutionCoordinatorError(
            "FAIL-CLOSED: invalid execution direction"
        )

    def _validate_execution(self, execution):
        if not isinstance(execution, dict):
            raise LiveExecutionCoordinatorError(
                "FAIL-CLOSED: execution contract must be an object"
            )

        if str(execution.get("mode", "")).strip().upper() != "LIVE":
            raise LiveExecutionCoordinatorError(
                "FAIL-CLOSED: coordinator requires mode=LIVE"
            )

        if execution.get("ready") is not True:
            raise LiveExecutionCoordinatorError(
                "FAIL-CLOSED: execution is not ready"
            )

        if execution.get("approved") is not True:
            raise LiveExecutionCoordinatorError(
                "FAIL-CLOSED: execution is not approved"
            )

        if str(execution.get("status", "")).strip().upper() != "EXECUTE":
            raise LiveExecutionCoordinatorError(
                "FAIL-CLOSED: execution status is not EXECUTE"
            )

        if str(execution.get("gate", "")).strip().upper() != "AUTHORIZED":
            raise LiveExecutionCoordinatorError(
                "FAIL-CLOSED: execution gate is not AUTHORIZED"
            )

        result = dict(execution)

        for field in (
            "authorization_id",
            "trade_uuid",
            "client_order_id",
            "symbol",
            "timeframe",
            "instrument_token",
            "decision",
        ):
            result[field] = self._string(
                execution.get(field),
                field,
            )

        result["decision"] = result["decision"].upper()

        if result["decision"] not in {"LONG", "SHORT"}:
            raise LiveExecutionCoordinatorError(
                "FAIL-CLOSED: invalid execution direction"
            )

        result["quantity"] = self._quantity(
            execution.get("quantity")
        )
        result["transaction_type"] = self._side(
            result["decision"]
        )

        return result

    @staticmethod
    def _broker_execution(execution):
        """Build an ephemeral broker-facing copy from canonical D2 execution."""
        decision_map = {
            "LONG": "ENTER_LONG",
            "SHORT": "ENTER_SHORT",
        }

        decision = str(execution.get("decision", "")).strip().upper()
        if decision not in decision_map:
            raise LiveExecutionCoordinatorError(
                "FAIL-CLOSED: invalid broker execution direction"
            )

        broker_execution = dict(execution)
        broker_execution["decision"] = decision_map[decision]
        broker_execution["position_size"] = execution["quantity"]
        broker_execution.pop("quantity", None)

        return broker_execution

    @staticmethod
    def _submission_id(authorization_id):
        return f"SUB:{authorization_id}"

    @staticmethod
    def _order_lineage_id(authorization_id):
        return f"{authorization_id}:ORDER:0"

    def _validate_existing_intent(self, row, execution):
        checks = (
            "trade_uuid",
            "client_order_id",
            "symbol",
            "timeframe",
            "mode",
            "decision",
        )

        for field in checks:
            left = str(row.get(field, "")).strip()
            right = str(execution.get(field, "")).strip()

            if field in {"mode", "decision"}:
                left = left.upper()
                right = right.upper()

            if left != right:
                raise LiveExecutionCoordinatorError(
                    "FAIL-CLOSED: execution intent identity mismatch"
                )

        if float(row["quantity"]) != float(execution["quantity"]):
            raise LiveExecutionCoordinatorError(
                "FAIL-CLOSED: execution intent quantity mismatch"
            )

    def _get_or_create_intent(self, execution):
        existing = self.db.get_execution_intent(
            execution["authorization_id"]
        )

        if existing is not None:
            row = dict(existing)
            self._validate_existing_intent(row, execution)
            return row

        now = self._now()

        self.db.insert_execution_intent({
            "authorization_id": execution["authorization_id"],
            "trade_uuid": execution["trade_uuid"],
            "client_order_id": execution["client_order_id"],
            "symbol": execution["symbol"],
            "timeframe": execution["timeframe"],
            "mode": "LIVE",
            "decision": execution["decision"],
            "quantity": execution["quantity"],
            "requested_price": execution.get("requested_price"),
            "stop_loss": execution.get("stop_loss"),
            "take_profit": execution.get("take_profit"),
            "run_id": execution.get("run_id"),
            "status": "AUTHORIZED",
            "created_at": now,
            "updated_at": now,
        })

        row = self.db.get_execution_intent(
            execution["authorization_id"]
        )

        if row is None:
            raise LiveExecutionCoordinatorError(
                "FAIL-CLOSED: execution intent persistence failed"
            )

        return dict(row)

    def _get_or_create_journal(self, execution):
        existing = self.db.get_execution_submission_by_client_order_id(
            execution["client_order_id"]
        )

        if existing is not None:
            row = dict(existing)

            if row["authorization_id"] != execution["authorization_id"]:
                raise LiveExecutionCoordinatorError(
                    "FAIL-CLOSED: submission authorization mismatch"
                )

            if row["instrument_token"] != execution["instrument_token"]:
                raise LiveExecutionCoordinatorError(
                    "FAIL-CLOSED: submission instrument mismatch"
                )

            if row["transaction_type"] != execution["transaction_type"]:
                raise LiveExecutionCoordinatorError(
                    "FAIL-CLOSED: submission direction mismatch"
                )

            if float(row["requested_qty"]) != float(execution["quantity"]):
                raise LiveExecutionCoordinatorError(
                    "FAIL-CLOSED: submission quantity mismatch"
                )

            return row

        now = self._now()

        self.db.insert_execution_submission({
            "submission_id": self._submission_id(
                execution["authorization_id"]
            ),
            "authorization_id": execution["authorization_id"],
            "trade_uuid": execution["trade_uuid"],
            "client_order_id": execution["client_order_id"],
            "symbol": execution["symbol"],
            "instrument_token": execution["instrument_token"],
            "transaction_type": execution["transaction_type"],
            "requested_qty": execution["quantity"],
            "status": "SUBMITTING",
            "created_at": now,
            "updated_at": now,
        })

        row = self.db.get_execution_submission_by_client_order_id(
            execution["client_order_id"]
        )

        if row is None:
            raise LiveExecutionCoordinatorError(
                "FAIL-CLOSED: submission journal persistence failed"
            )

        return dict(row)

    def _result(
        self,
        execution,
        status,
        broker_order_id=None,
        *,
        action=None,
        reason=None,
    ):
        result = {
            "authorization_id": execution["authorization_id"],
            "client_order_id": execution["client_order_id"],
            "status": status,
            "broker_order_id": broker_order_id,
        }

        if action is not None:
            result["action"] = action

        if reason is not None:
            result["reason"] = reason

        return result

    def _persist_lineage(self, execution, journal):
        broker_order_id = str(
            journal.get("broker_order_id") or ""
        ).strip()

        if not broker_order_id:
            raise LiveExecutionCoordinatorError(
                "FAIL-CLOSED: missing broker_order_id"
            )

        existing = self.db.get_execution_order_by_broker_id(
            broker_order_id
        )

        if existing is not None:
            durable = dict(existing)

            identity_checks = (
                ("authorization_id", execution["authorization_id"]),
                ("client_order_id", execution["client_order_id"]),
                ("trade_uuid", execution["trade_uuid"]),
                ("instrument_token", execution["instrument_token"]),
                ("transaction_type", execution["transaction_type"]),
            )

            for field, expected in identity_checks:
                if str(durable[field]).strip() != str(expected).strip():
                    raise LiveExecutionCoordinatorError(
                        "FAIL-CLOSED: existing durable order identity mismatch"
                    )

            if float(durable["requested_qty"]) != float(
                execution["quantity"]
            ):
                raise LiveExecutionCoordinatorError(
                    "FAIL-CLOSED: existing durable order quantity mismatch"
                )

        else:
            now = self._now()

            self.db.insert_execution_order({
                "order_lineage_id": self._order_lineage_id(
                    execution["authorization_id"]
                ),
                "authorization_id": execution["authorization_id"],
                "trade_uuid": execution["trade_uuid"],
                "client_order_id": execution["client_order_id"],
                "broker_order_id": broker_order_id,
                "child_index": 0,
                "instrument_token": execution["instrument_token"],
                "transaction_type": execution["transaction_type"],
                "requested_qty": execution["quantity"],
                "filled_qty": 0.0,
                "remaining_qty": execution["quantity"],
                "average_fill_price": None,
                "status": "SUBMITTED",
                "raw_status": "SUBMITTED",
                "created_at": now,
                "updated_at": now,
            })

        journal_status = str(
            journal.get("status", "")
        ).strip().upper()

        if journal_status != "LINEAGE_PERSISTED":
            self.db.update_execution_submission(
                journal["submission_id"],
                status="LINEAGE_PERSISTED",
                broker_order_id=broker_order_id,
            )

        parent = self.db.get_execution_intent(
            execution["authorization_id"]
        )

        if parent is None:
            raise LiveExecutionCoordinatorError(
                "FAIL-CLOSED: parent execution intent disappeared"
            )

        parent_status = str(parent["status"]).strip().upper()

        if parent_status in {
            "AUTHORIZED",
            "SUBMITTING",
        }:
            self.db.update_execution_intent(
                execution["authorization_id"],
                status="SUBMITTED",
            )
            parent_status = "SUBMITTED"

        elif parent_status not in {
            "SUBMITTED",
            "PARTIAL",
            "FILLED",
            "POSITION_RECONCILING",
            "PROTECTION_PENDING",
            "RECONCILED",
        }:
            raise LiveExecutionCoordinatorError(
                "FAIL-CLOSED: incompatible parent state for durable lineage"
            )

        return self._result(
            execution,
            parent_status,
            broker_order_id,
            action="LINEAGE_PERSISTED",
        )

    @staticmethod
    def _normalize_history(record, journal, execution):
        if not isinstance(record, dict):
            raise LiveExecutionCoordinatorError(
                "FAIL-CLOSED: malformed broker history record"
            )

        broker_id = str(
            record.get("broker_order_id")
            or record.get("order_id")
            or ""
        ).strip()

        if not broker_id:
            raise LiveExecutionCoordinatorError(
                "FAIL-CLOSED: broker history missing order identity"
            )

        tag = str(
            record.get("client_order_id")
            or record.get("tag")
            or ""
        ).strip()

        if tag != str(journal["client_order_id"]).strip():
            raise LiveExecutionCoordinatorError(
                "FAIL-CLOSED: broker history tag mismatch"
            )

        token = str(
            record.get("instrument_token") or ""
        ).strip()

        if token != str(journal["instrument_token"]).strip():
            raise LiveExecutionCoordinatorError(
                "FAIL-CLOSED: broker history instrument mismatch"
            )

        side = str(
            record.get("transaction_type")
            or record.get("side")
            or ""
        ).strip().upper()

        if side != str(journal["transaction_type"]).strip().upper():
            raise LiveExecutionCoordinatorError(
                "FAIL-CLOSED: broker history direction mismatch"
            )

        try:
            quantity = float(
                record.get("requested_qty")
                if record.get("requested_qty") is not None
                else record.get("quantity")
            )
        except (TypeError, ValueError) as exc:
            raise LiveExecutionCoordinatorError(
                "FAIL-CLOSED: broker history quantity invalid"
            ) from exc

        expected = float(journal["requested_qty"])

        if quantity != expected:
            raise LiveExecutionCoordinatorError(
                "FAIL-CLOSED: broker history quantity mismatch"
            )

        return {
            "broker_order_id": broker_id,
            "authorization_id": execution["authorization_id"],
            "client_order_id": journal["client_order_id"],
            "symbol": journal["symbol"],
            "instrument_token": journal["instrument_token"],
            "transaction_type": journal["transaction_type"],
            "requested_qty": quantity,
        }

    def start_submission(self, execution):
        execution = self._validate_execution(execution)

        intent = self._get_or_create_intent(execution)
        journal = self._get_or_create_journal(execution)

        journal_status = str(journal["status"]).strip().upper()

        if journal_status == self.JOURNAL_LINEAGE_PERSISTED:
            return self._persist_lineage(
                execution,
                journal,
            )

        if journal_status == self.JOURNAL_HALTED:
            return self._result(
                execution,
                "HALTED",
                journal.get("broker_order_id"),
                action="UNCHANGED_HALTED",
                reason=journal.get("error_reason"),
            )

        if journal_status == self.JOURNAL_IDENTIFIED:
            return self._persist_lineage(
                execution,
                journal,
            )

        if journal_status != self.JOURNAL_SUBMITTING:
            raise LiveExecutionCoordinatorError(
                "FAIL-CLOSED: unsupported submission journal state"
            )

        parent_status = str(intent["status"]).strip().upper()

        if parent_status == "AUTHORIZED":
            self.db.update_execution_intent(
                execution["authorization_id"],
                status="SUBMITTING",
            )
            parent_status = "SUBMITTING"

        elif parent_status == "SUBMITTED":
            # A prior broker submission may already exist. Never resubmit.
            return self._result(
                execution,
                "SUBMITTED",
                journal.get("broker_order_id"),
                action="PARENT_ALREADY_SUBMITTED",
            )

        elif parent_status == "HALTED":
            return self._result(
                execution,
                "HALTED",
                journal.get("broker_order_id"),
                action="UNCHANGED_HALTED",
            )

        elif parent_status != "SUBMITTING":
            raise LiveExecutionCoordinatorError(
                "FAIL-CLOSED: parent state conflicts with submission journal"
            )

        if journal.get("broker_order_id"):
            return self._persist_lineage(
                execution,
                journal,
            )

        try:
            broker_execution = self._broker_execution(execution)
            submission = self.broker.submit_entry(
                broker_execution
            )
        except Exception as exc:
            # Do not resubmit. The broker may have accepted the request
            # while the response was lost.
            return self._result(
                execution,
                "SUBMITTING",
                action="RECOVERY_REQUIRED",
                reason=type(exc).__name__,
            )

        if not isinstance(submission, dict):
            raise LiveExecutionCoordinatorError(
                "FAIL-CLOSED: broker submission result is not an object"
            )

        broker_id = str(
            submission.get("broker_order_id") or ""
        ).strip()

        if not broker_id:
            raise LiveExecutionCoordinatorError(
                "FAIL-CLOSED: broker submission returned no identity"
            )

        self.db.update_execution_submission(
            journal["submission_id"],
            status="IDENTIFIED",
            broker_order_id=broker_id,
        )

        refreshed = self.db.get_execution_submission(
            journal["submission_id"]
        )

        return self._persist_lineage(
            execution,
            dict(refreshed),
        )

    def recover_submission(self, authorization_id):
        if (
            not isinstance(authorization_id, str)
            or not authorization_id.strip()
        ):
            raise LiveExecutionCoordinatorError(
                "FAIL-CLOSED: invalid authorization_id"
            )

        authorization_id = authorization_id.strip()

        intent_row = self.db.get_execution_intent(
            authorization_id
        )

        if intent_row is None:
            raise LiveExecutionCoordinatorError(
                "FAIL-CLOSED: execution intent not found"
            )

        intent = dict(intent_row)

        if str(intent["mode"]).strip().upper() != "LIVE":
            raise LiveExecutionCoordinatorError(
                "FAIL-CLOSED: recovery requires mode=LIVE"
            )

        journal_row = self.db.get_execution_submission_by_client_order_id(
            intent["client_order_id"]
        )

        if journal_row is None:
            raise LiveExecutionCoordinatorError(
                "FAIL-CLOSED: submission journal not found"
            )

        journal = dict(journal_row)

        if journal["authorization_id"] != authorization_id:
            raise LiveExecutionCoordinatorError(
                "FAIL-CLOSED: journal authorization mismatch"
            )

        recovery_execution = dict(intent)
        recovery_execution["instrument_token"] = journal["instrument_token"]
        recovery_execution["transaction_type"] = journal["transaction_type"]

        status = str(journal["status"]).strip().upper()

        if status == self.JOURNAL_LINEAGE_PERSISTED:
            return self._persist_lineage(
                recovery_execution,
                journal,
            )

        if status == self.JOURNAL_HALTED:
            return self._result(
                intent,
                "HALTED",
                journal.get("broker_order_id"),
                action="UNCHANGED_HALTED",
                reason=journal.get("error_reason"),
            )

        if status == self.JOURNAL_IDENTIFIED:
            return self._persist_lineage(
                recovery_execution,
                journal,
            )

        if status != self.JOURNAL_SUBMITTING:
            raise LiveExecutionCoordinatorError(
                "FAIL-CLOSED: unsupported recovery journal state"
            )

        history = self.broker.get_order_history(
            client_order_id=journal["client_order_id"]
        )

        if history is None:
            history = []

        if not isinstance(history, list):
            history = [history]

        if len(history) != 1:
            reason = (
                "No unique broker order found for submission tag"
                if len(history) == 0
                else "Multiple broker orders found for submission tag"
            )

            parent = self.db.get_execution_intent(
                authorization_id
            )

            if parent is not None and str(
                parent["status"]
            ).strip().upper() in {
                "AUTHORIZED",
                "SUBMITTING",
            }:
                self.db.update_execution_intent(
                    authorization_id,
                    status="HALTED",
                )

            self.db.update_execution_submission(
                journal["submission_id"],
                status="HALTED",
                error_reason=reason,
            )

            return self._result(
                intent,
                "HALTED",
                action="HALTED",
                reason=reason,
            )

        try:
            normalized = self._normalize_history(
                history[0],
                journal,
                intent,
            )
        except Exception as exc:
            parent = self.db.get_execution_intent(
                authorization_id
            )

            if parent is not None and str(
                parent["status"]
            ).strip().upper() in {
                "AUTHORIZED",
                "SUBMITTING",
            }:
                self.db.update_execution_intent(
                    authorization_id,
                    status="HALTED",
                )

            self.db.update_execution_submission(
                journal["submission_id"],
                status="HALTED",
                error_reason=str(exc),
            )

            return self._result(
                intent,
                "HALTED",
                action="HALTED",
                reason=str(exc),
            )

        self.db.update_execution_submission(
            journal["submission_id"],
            status="IDENTIFIED",
            broker_order_id=normalized["broker_order_id"],
        )

        refreshed = self.db.get_execution_submission(
            journal["submission_id"]
        )

        return self._persist_lineage(
            recovery_execution,
            dict(refreshed),
        )
