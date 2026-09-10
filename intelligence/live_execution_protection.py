"""Isolated LIVE execution-protection submission boundary.

This module provides the durable submission boundary for V9 execution
protections. It is intentionally not wired into main.py or ExecutionAdapter.

Safety properties:
- protection intent is durably recorded as PENDING before broker submission
- an existing ambiguous PENDING protection is never blindly resubmitted
- broker identity is persisted before downstream reconciliation
- ambiguous recovery uses deterministic broker history tags
- zero or multiple recovery matches fail closed
- no PAPER fallback
"""

from datetime import datetime
import math


class LiveExecutionProtectionError(RuntimeError):
    """Raised when LIVE protection execution cannot proceed safely."""


class LiveExecutionProtectionService:
    """Durable one-shot LIVE protection submission and recovery boundary."""

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

    def __init__(self, broker, *, database_module):
        if broker is None:
            raise LiveExecutionProtectionError(
                "FAIL-CLOSED: explicit LIVE broker is required"
            )

        if str(
            getattr(broker, "EXECUTION_MODE", "")
        ).strip().upper() != "LIVE":
            raise LiveExecutionProtectionError(
                "FAIL-CLOSED: protection service requires LIVE broker"
            )

        for name in (
            "submit_protection",
            "get_order_history",
        ):
            if not callable(getattr(broker, name, None)):
                raise LiveExecutionProtectionError(
                    "FAIL-CLOSED: LIVE broker API unavailable: "
                    f"{name}"
                )

        if database_module is None:
            raise LiveExecutionProtectionError(
                "FAIL-CLOSED: database module is required"
            )

        for name in (
            "get_execution_intent",
            "list_execution_protections",
            "insert_execution_protection",
            "update_execution_protection",
            "update_execution_intent",
        ):
            if not callable(getattr(database_module, name, None)):
                raise LiveExecutionProtectionError(
                    "FAIL-CLOSED: database API unavailable: "
                    f"{name}"
                )

        self.broker = broker
        self.db = database_module

    @staticmethod
    def _required_string(value, field):
        if not isinstance(value, str) or not value.strip():
            raise LiveExecutionProtectionError(
                f"FAIL-CLOSED: invalid {field}"
            )
        return value.strip()

    @staticmethod
    def _positive_quantity(value):
        try:
            quantity = float(value)
        except (TypeError, ValueError) as exc:
            raise LiveExecutionProtectionError(
                "FAIL-CLOSED: invalid protection quantity"
            ) from exc

        if not math.isfinite(quantity) or quantity <= 0:
            raise LiveExecutionProtectionError(
                "FAIL-CLOSED: protection quantity must be finite and positive"
            )

        return quantity

    @staticmethod
    def _positive_price(value):
        try:
            price = float(value)
        except (TypeError, ValueError) as exc:
            raise LiveExecutionProtectionError(
                "FAIL-CLOSED: invalid protection price"
            ) from exc

        if not math.isfinite(price) or price <= 0:
            raise LiveExecutionProtectionError(
                "FAIL-CLOSED: protection price must be finite and positive"
            )

        return price

    @staticmethod
    def _now():
        return datetime.utcnow().isoformat()

    @staticmethod
    def _protection_id(authorization_id, protection_type, target_index):
        suffix = (
            "SL"
            if protection_type == "STOP_LOSS"
            else f"TP{target_index}"
        )
        return f"{authorization_id}:PROTECTION:{suffix}"

    @staticmethod
    def _tag(client_order_id, protection_type, target_index):
        suffix = (
            "SL"
            if protection_type == "STOP_LOSS"
            else f"TP{target_index + 1}"
        )
        tag = f"{client_order_id}-{suffix}"

        if len(tag) > 40:
            tag = f"{client_order_id[:35]}-{suffix}"

        if len(tag) > 40:
            raise LiveExecutionProtectionError(
                "FAIL-CLOSED: protection broker tag exceeds limit"
            )

        return tag

    def _resolve_instrument_token(self, authorization_id):
        rows = self.db.list_execution_orders(
            authorization_id
        )

        if rows is None:
            rows = []

        if not isinstance(rows, (list, tuple)):
            raise LiveExecutionProtectionError(
                "FAIL-CLOSED: execution order lineage must be a sequence"
            )

        if not rows:
            raise LiveExecutionProtectionError(
                "FAIL-CLOSED: execution order lineage not found"
            )

        tokens = set()

        for row in rows:
            if not isinstance(row, dict):
                row = dict(row)

            token = row.get("instrument_token")

            if (
                not isinstance(token, str)
                or not token.strip()
            ):
                raise LiveExecutionProtectionError(
                    "FAIL-CLOSED: execution order lineage missing instrument_token"
                )

            tokens.add(token.strip())

        if len(tokens) != 1:
            raise LiveExecutionProtectionError(
                "FAIL-CLOSED: execution order lineage has ambiguous instrument identity"
            )

        return next(iter(tokens))

    def _load_live_intent(self, authorization_id):
        row = self.db.get_execution_intent(
            authorization_id
        )

        if row is None:
            raise LiveExecutionProtectionError(
                "FAIL-CLOSED: execution intent not found"
            )

        intent = dict(row)

        if self._required_string(
            intent.get("authorization_id"),
            "authorization_id",
        ) != authorization_id:
            raise LiveExecutionProtectionError(
                "FAIL-CLOSED: execution intent authorization mismatch"
            )

        if str(
            intent.get("mode", "")
        ).strip().upper() != "LIVE":
            raise LiveExecutionProtectionError(
                "FAIL-CLOSED: protection execution requires mode=LIVE"
            )

        for field in (
            "trade_uuid",
            "client_order_id",
            "symbol",
            "timeframe",
            "decision",
        ):
            self._required_string(
                intent.get(field),
                field,
            )

        decision = str(
            intent.get("decision", "")
        ).strip().upper()

        if decision not in {"LONG", "SHORT"}:
            raise LiveExecutionProtectionError(
                "FAIL-CLOSED: invalid execution decision"
            )

        self._positive_quantity(
            intent.get("quantity")
        )
        self._positive_price(
            intent.get("stop_loss")
        )
        self._positive_price(
            intent.get("take_profit")
        )

        status = str(
            intent.get("status", "")
        ).strip().upper()

        if status != "PROTECTION_PENDING":
            raise LiveExecutionProtectionError(
                "FAIL-CLOSED: protection submission requires "
                "parent PROTECTION_PENDING"
            )

        instrument_token = self._resolve_instrument_token(
            authorization_id
        )

        # The token is authoritative durable lineage, but this copy is
        # ephemeral and exists only for broker-facing validation/submission.
        intent["instrument_token"] = instrument_token

        return intent

    def ensure_protections(self, authorization_id):
        """Create the durable LIVE SL and TP protection intents."""
        authorization_id = self._required_string(
            authorization_id,
            "authorization_id",
        )

        intent = self._load_live_intent(
            authorization_id
        )

        quantity = self._positive_quantity(
            intent.get("quantity")
        )

        stop_loss = self._positive_price(
            intent.get("stop_loss")
        )

        take_profit = self._positive_price(
            intent.get("take_profit")
        )

        existing_rows = self.db.list_execution_protections(
            authorization_id
        )

        if existing_rows is None:
            existing_rows = []

        if not isinstance(existing_rows, (list, tuple)):
            raise LiveExecutionProtectionError(
                "FAIL-CLOSED: protection lineage must be a sequence"
            )

        existing = {
            str(row["protection_id"]): dict(row)
            for row in existing_rows
        }

        now = self._now()

        definitions = (
            (
                "STOP_LOSS",
                0,
                stop_loss,
            ),
            (
                "TAKE_PROFIT",
                0,
                take_profit,
            ),
        )

        created = []

        for protection_type, target_index, requested_price in definitions:
            protection_id = self._protection_id(
                authorization_id,
                protection_type,
                target_index,
            )

            if protection_id in existing:
                row = existing[protection_id]

                if str(
                    row.get("protection_type", "")
                ).strip().upper() != protection_type:
                    raise LiveExecutionProtectionError(
                        "FAIL-CLOSED: protection identity mismatch"
                    )

                if float(row.get("requested_qty")) != quantity:
                    raise LiveExecutionProtectionError(
                        "FAIL-CLOSED: protection quantity mismatch"
                    )

                if float(row.get("requested_price")) != requested_price:
                    raise LiveExecutionProtectionError(
                        "FAIL-CLOSED: protection price mismatch"
                    )

                continue

            self.db.insert_execution_protection(
                {
                    "protection_id": protection_id,
                    "authorization_id": authorization_id,
                    "protection_type": protection_type,
                    "target_index": target_index,
                    "broker_order_id": None,
                    "requested_qty": quantity,
                    "verified_qty": None,
                    "requested_price": requested_price,
                    "verified_price": None,
                    "status": "PENDING",
                    "created_at": now,
                    "updated_at": now,
                }
            )

            created.append(protection_id)

        return {
            "authorization_id": authorization_id,
            "status": "PENDING",
            "created_protections": created,
        }

    def _find_protection(
        self,
        authorization_id,
        protection_id,
    ):
        rows = self.db.list_execution_protections(
            authorization_id
        )

        if rows is None:
            rows = []

        for row in rows:
            current = dict(row)

            if current.get("protection_id") == protection_id:
                return current

        raise LiveExecutionProtectionError(
            "FAIL-CLOSED: protection lineage not found"
        )

    def submit_pending_protection(
        self,
        authorization_id,
        protection_id,
    ):
        """Submit a newly created PENDING protection exactly once."""
        authorization_id = self._required_string(
            authorization_id,
            "authorization_id",
        )

        protection_id = self._required_string(
            protection_id,
            "protection_id",
        )

        intent = self._load_live_intent(
            authorization_id
        )

        protection = self._find_protection(
            authorization_id,
            protection_id,
        )

        status = str(
            protection.get("status", "")
        ).strip().upper()

        if status in self.TERMINAL_PROTECTION_STATES:
            return {
                "authorization_id": authorization_id,
                "protection_id": protection_id,
                "status": status,
                "action": "UNCHANGED_TERMINAL",
            }

        broker_order_id = protection.get(
            "broker_order_id"
        )

        if broker_order_id:
            return {
                "authorization_id": authorization_id,
                "protection_id": protection_id,
                "broker_order_id": broker_order_id,
                "status": status,
                "action": "IDENTITY_ALREADY_PERSISTED",
            }

        if status != "PENDING":
            raise LiveExecutionProtectionError(
                "FAIL-CLOSED: unsupported protection submission state"
            )

        raise LiveExecutionProtectionError(
            "FAIL-CLOSED: existing PENDING protection is ambiguous; "
            "recovery is required before any broker submission"
        )

    def submit_new_protection(
        self,
        authorization_id,
        protection_type,
        target_index=0,
    ):
        """Create and submit exactly one previously absent protection."""
        authorization_id = self._required_string(
            authorization_id,
            "authorization_id",
        )

        protection_type = self._required_string(
            protection_type,
            "protection_type",
        ).upper()

        if protection_type not in {
            "STOP_LOSS",
            "TAKE_PROFIT",
        }:
            raise LiveExecutionProtectionError(
                "FAIL-CLOSED: invalid protection type"
            )

        if isinstance(target_index, bool):
            raise LiveExecutionProtectionError(
                "FAIL-CLOSED: invalid protection target_index"
            )

        try:
            target_index = int(target_index)
        except (TypeError, ValueError, OverflowError) as exc:
            raise LiveExecutionProtectionError(
                "FAIL-CLOSED: invalid protection target_index"
            ) from exc

        if target_index < 0:
            raise LiveExecutionProtectionError(
                "FAIL-CLOSED: invalid protection target_index"
            )

        intent = self._load_live_intent(
            authorization_id
        )

        quantity = self._positive_quantity(
            intent.get("quantity")
        )

        requested_price = (
            intent.get("stop_loss")
            if protection_type == "STOP_LOSS"
            else intent.get("take_profit")
        )

        requested_price = self._positive_price(
            requested_price
        )

        protection_id = self._protection_id(
            authorization_id,
            protection_type,
            target_index,
        )

        existing = self.db.list_execution_protections(
            authorization_id
        ) or []

        for row in existing:
            current = dict(row)

            if current.get("protection_id") == protection_id:
                return self.submit_pending_protection(
                    authorization_id,
                    protection_id,
                )

        now = self._now()

        protection = {
            "protection_id": protection_id,
            "authorization_id": authorization_id,
            "protection_type": protection_type,
            "target_index": target_index,
            "broker_order_id": None,
            "requested_qty": quantity,
            "verified_qty": None,
            "requested_price": requested_price,
            "verified_price": None,
            "status": "PENDING",
            "created_at": now,
            "updated_at": now,
        }

        self.db.insert_execution_protection(
            protection
        )

        try:
            result = self.broker.submit_protection(
                intent,
                protection,
            )
        except Exception as exc:
            return {
                "authorization_id": authorization_id,
                "protection_id": protection_id,
                "status": "PENDING",
                "action": "RECOVERY_REQUIRED",
                "reason": type(exc).__name__,
            }

        if not isinstance(result, dict):
            raise LiveExecutionProtectionError(
                "FAIL-CLOSED: protection submission result is invalid"
            )

        broker_order_id = self._required_string(
            result.get("broker_order_id"),
            "broker_order_id",
        )

        try:
            self.db.update_execution_protection(
                protection_id,
                broker_order_id=broker_order_id,
            )
        except Exception as exc:
            raise LiveExecutionProtectionError(
                "FAIL-CLOSED: protection submitted but "
                "broker identity persistence failed"
            ) from exc

        return {
            "authorization_id": authorization_id,
            "protection_id": protection_id,
            "broker_order_id": broker_order_id,
            "status": "PENDING",
            "action": "IDENTIFIED",
        }

    def recover_pending_protection(
        self,
        authorization_id,
        protection_id,
    ):
        """Recover a PENDING protection without resubmitting it."""
        authorization_id = self._required_string(
            authorization_id,
            "authorization_id",
        )

        protection_id = self._required_string(
            protection_id,
            "protection_id",
        )

        intent = self._load_live_intent(
            authorization_id
        )

        protection = self._find_protection(
            authorization_id,
            protection_id,
        )

        status = str(
            protection.get("status", "")
        ).strip().upper()

        if status in self.TERMINAL_PROTECTION_STATES:
            return {
                "authorization_id": authorization_id,
                "protection_id": protection_id,
                "status": status,
                "action": "UNCHANGED_TERMINAL",
            }

        persisted_broker_id = protection.get(
            "broker_order_id"
        )

        if persisted_broker_id:
            return {
                "authorization_id": authorization_id,
                "protection_id": protection_id,
                "broker_order_id": persisted_broker_id,
                "status": status,
                "action": "IDENTITY_ALREADY_PERSISTED",
            }

        if status != "PENDING":
            raise LiveExecutionProtectionError(
                "FAIL-CLOSED: unsupported protection recovery state"
            )

        protection_type = str(
            protection.get("protection_type", "")
        ).strip().upper()

        if protection_type not in {
            "STOP_LOSS",
            "TAKE_PROFIT",
        }:
            raise LiveExecutionProtectionError(
                "FAIL-CLOSED: invalid protection type"
            )

        raw_target_index = protection.get("target_index")
        if isinstance(raw_target_index, bool):
            raise LiveExecutionProtectionError(
                "FAIL-CLOSED: invalid protection target_index"
            )

        try:
            target_index = int(raw_target_index)
        except (TypeError, ValueError, OverflowError) as exc:
            raise LiveExecutionProtectionError(
                "FAIL-CLOSED: invalid protection target_index"
            ) from exc

        if target_index < 0:
            raise LiveExecutionProtectionError(
                "FAIL-CLOSED: invalid protection target_index"
            )

        self._positive_quantity(
            protection.get("requested_qty")
        )
        self._positive_price(
            protection.get("requested_price")
        )

        tag = self._tag(
            intent["client_order_id"],
            protection_type,
            target_index,
        )

        try:
            history = self.broker.get_order_history(
                client_order_id=tag
            )
        except Exception as exc:
            return {
                "authorization_id": authorization_id,
                "protection_id": protection_id,
                "status": "PENDING",
                "action": "RECOVERY_REQUIRED",
                "reason": type(exc).__name__,
            }

        if history is None:
            history = []

        if not isinstance(history, list):
            history = [history]

        if len(history) != 1:
            reason = (
                "No unique broker protection found by tag"
                if len(history) == 0
                else "Multiple broker protections found by tag"
            )

            try:
                self.db.update_execution_protection(
                    protection_id,
                    status="HALTED",
                )
            except Exception as exc:
                raise LiveExecutionProtectionError(
                    "FAIL-CLOSED: unable to persist HALTED protection"
                ) from exc

            try:
                self.db.update_execution_intent(
                    authorization_id,
                    status="HALTED",
                )
            except Exception as exc:
                raise LiveExecutionProtectionError(
                    "FAIL-CLOSED: unable to persist HALTED parent"
                ) from exc

            return {
                "authorization_id": authorization_id,
                "protection_id": protection_id,
                "status": "HALTED",
                "action": "HALTED",
                "reason": reason,
            }

        observed = history[0]

        if not isinstance(observed, dict):
            raise LiveExecutionProtectionError(
                "FAIL-CLOSED: malformed broker protection history"
            )

        broker_order_id = (
            observed.get("broker_order_id")
            or observed.get("order_id")
        )

        broker_order_id = self._required_string(
            broker_order_id,
            "broker_order_id",
        )

        observed_tag = str(
            observed.get("tag", "")
        ).strip()

        if observed_tag and observed_tag != tag:
            raise LiveExecutionProtectionError(
                "FAIL-CLOSED: broker protection tag mismatch"
            )

        observed_token = str(
            observed.get("instrument_token", "")
        ).strip()

        intent_token = str(
            intent.get("instrument_token", "")
        ).strip()

        if not observed_token or observed_token != intent_token:
            raise LiveExecutionProtectionError(
                "FAIL-CLOSED: broker protection instrument mismatch"
            )

        expected_side = (
            "SELL"
            if str(intent["decision"]).upper().strip() == "LONG"
            else "BUY"
        )

        observed_side = str(
            observed.get("transaction_type", "")
        ).upper().strip()

        if observed_side != expected_side:
            raise LiveExecutionProtectionError(
                "FAIL-CLOSED: broker protection direction mismatch"
            )

        try:
            observed_qty = float(
                observed.get("quantity")
            )
            expected_qty = float(
                protection.get("requested_qty")
            )
        except (TypeError, ValueError) as exc:
            raise LiveExecutionProtectionError(
                "FAIL-CLOSED: broker protection quantity invalid"
            ) from exc

        if observed_qty != expected_qty:
            raise LiveExecutionProtectionError(
                "FAIL-CLOSED: broker protection quantity mismatch"
            )

        order_type = str(
            observed.get("order_type", "")
        ).upper().strip()

        if protection_type == "STOP_LOSS":
            if order_type not in {"SL", "SL-M"}:
                raise LiveExecutionProtectionError(
                    "FAIL-CLOSED: broker stop-loss order type mismatch"
                )
        else:
            if order_type != "LIMIT":
                raise LiveExecutionProtectionError(
                    "FAIL-CLOSED: broker take-profit order type mismatch"
                )

        requested_price = float(
            protection["requested_price"]
        )

        if protection_type == "STOP_LOSS":
            observed_price = float(
                observed.get("trigger_price")
            )
        else:
            observed_price = float(
                observed.get("price")
            )

        if observed_price != requested_price:
            raise LiveExecutionProtectionError(
                "FAIL-CLOSED: broker protection price mismatch"
            )

        try:
            self.db.update_execution_protection(
                protection_id,
                broker_order_id=broker_order_id,
            )
        except Exception as exc:
            raise LiveExecutionProtectionError(
                "FAIL-CLOSED: recovered broker identity persistence failed"
            ) from exc

        return {
            "authorization_id": authorization_id,
            "protection_id": protection_id,
            "broker_order_id": broker_order_id,
            "status": "PENDING",
            "action": "RECOVERED_IDENTITY",
        }
