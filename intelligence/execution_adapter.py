"""
Jaguar Quant X
Execution Adapter

Explicit boundary between enterprise execution authorization
and downstream execution.

PAPER is enabled.
LIVE is permanently fail-closed until explicitly implemented.
"""

from intelligence.paper_broker_adapter import PaperBrokerAdapter


class ExecutionAdapter:

    PAPER = "PAPER"
    LIVE = "LIVE"

    def __init__(self, mode=PAPER, broker=None):
        mode = str(mode).upper().strip()

        if mode not in (
            self.PAPER,
            self.LIVE,
        ):
            raise ValueError(
                f"Invalid execution mode: {mode}"
            )

        self.mode = mode

        if broker is None:
            if mode != self.PAPER:
                raise RuntimeError(
                    "FAIL-CLOSED: LIVE execution requires an explicit "
                    "LIVE broker"
                )
            broker = PaperBrokerAdapter()

        broker_mode = str(
            getattr(
                broker,
                "EXECUTION_MODE",
                "",
            )
        ).upper().strip()

        if broker_mode != mode:
            raise RuntimeError(
                "FAIL-CLOSED: Execution mode does not match broker mode"
            )

        self.broker = broker

    def authorize(self, execution):
        if not isinstance(execution, dict):
            raise RuntimeError(
                "FAIL-CLOSED: Invalid execution contract"
            )

        execution_mode = str(
            execution.get(
                "mode",
                self.PAPER,
            )
        ).upper().strip()

        if execution_mode != self.mode:
            raise RuntimeError(
                "FAIL-CLOSED: Execution mode does not match adapter mode"
            )

        if self.mode == self.LIVE:
            raise RuntimeError(
                "FAIL-CLOSED: LIVE execution is disabled"
            )

        if not (
            execution.get("ready") is True
            and execution.get("approved") is True
            and execution.get("status") == "EXECUTE"
            and execution.get("gate") == "AUTHORIZED"
        ):
            raise RuntimeError(
                "FAIL-CLOSED: Execution contract is not authorized"
            )

        return {
            "mode": self.PAPER,
            "authorized": True,
            "execution": dict(execution),
        }

    def rollback(self, execution_result, price=None):
        """
        Fail-closed rollback for an already executed paper entry.

        This is a compensating action for downstream persistence failures.
        It does not create or modify trading authority.
        """
        if not isinstance(execution_result, dict):
            raise RuntimeError(
                "FAIL-CLOSED: Invalid execution result for rollback"
            )

        authorization_id = execution_result.get(
            "authorization_id"
        )

        if not authorization_id:
            raise RuntimeError(
                "FAIL-CLOSED: Missing authorization_id for rollback"
            )

        order = self.broker.get_order(
            authorization_id
        )

        if order is None:
            raise RuntimeError(
                "FAIL-CLOSED: Paper order missing during rollback"
            )

        position = self.broker.get_position(
            authorization_id
        )

        if position is None:
            return {
                "status": self.broker.CLOSED,
                "authorization_id": authorization_id,
                "rolled_back": True,
            }

        if price is None:
            price = order.get(
                "average_fill_price",
                0.0,
            )

        rollback = self.broker.close_position(
            authorization_id,
            price,
        )

        if rollback.get("status") != self.broker.CLOSED:
            raise RuntimeError(
                "FAIL-CLOSED: Paper execution rollback failed"
            )

        return {
            "status": self.broker.CLOSED,
            "authorization_id": authorization_id,
            "rolled_back": True,
            "position": rollback,
        }


    def execute(self, execution, fill_quantity=None):
        authorization = self.authorize(execution)

        contract = authorization["execution"]

        order = self.broker.submit_entry(
            contract,
            fill_quantity=fill_quantity,
        )

        if order.get("status") not in (
            "FILLED",
            "PARTIALLY_FILLED",
        ):
            raise RuntimeError(
                "FAIL-CLOSED: Paper entry rejected"
            )

        requested_quantity = float(
            order.get("requested_qty", 0.0)
        )

        filled_quantity = float(
            order.get("filled_qty", 0.0)
        )

        remaining_quantity = float(
            order.get("remaining_qty", 0.0)
        )

        if requested_quantity <= 0:
            raise RuntimeError(
                "FAIL-CLOSED: Paper requested quantity invalid"
            )

        if filled_quantity <= 0:
            raise RuntimeError(
                "FAIL-CLOSED: Paper fill quantity invalid"
            )

        if remaining_quantity > 0:
            cancelled = self.broker.cancel_entry(
                contract["authorization_id"]
            )

            if cancelled.get("status") != "CANCELLED":
                rollback = self.broker.close_position(
                    contract["authorization_id"],
                    contract.get("entry", 0.0),
                )

                if rollback.get("status") != self.broker.CLOSED:
                    raise RuntimeError(
                        "FAIL-CLOSED: Residual cancellation failed "
                        "AND rollback failed"
                    )

                raise RuntimeError(
                    "FAIL-CLOSED: Residual cancellation failed; "
                    "paper entry rolled back"
                )

            remaining_quantity = float(
                cancelled.get("remaining_qty", 0.0)
            )

            if remaining_quantity != 0.0:
                rollback = self.broker.close_position(
                    contract["authorization_id"],
                    contract.get("entry", 0.0),
                )

                if rollback.get("status") != self.broker.CLOSED:
                    raise RuntimeError(
                        "FAIL-CLOSED: Residual quantity remains "
                        "AND rollback failed"
                    )

                raise RuntimeError(
                    "FAIL-CLOSED: Residual quantity remains "
                    "after cancellation; paper entry rolled back"
                )

        authorization_id = contract["authorization_id"]

        protection = self.broker.submit_protection(
            contract,
            filled_quantity,
        )

        if protection.get("status") != "OPEN":
            rollback = self.broker.close_position(
                authorization_id,
                contract.get("entry", 0.0),
            )

            if rollback.get("status") != self.broker.CLOSED:
                raise RuntimeError(
                    "FAIL-CLOSED: Paper protection rejected "
                    "AND rollback failed"
                )

            raise RuntimeError(
                "FAIL-CLOSED: Paper protection rejected; "
                "paper entry rolled back"
            )

        position_reconciliation = self.broker.reconcile(
            authorization_id,
            filled_quantity,
        )

        if not position_reconciliation.get(
            "reconciled"
        ):
            rollback = self.broker.close_position(
                authorization_id,
                contract.get("entry", 0.0),
            )

            if rollback.get("status") != self.broker.CLOSED:
                raise RuntimeError(
                    "FAIL-CLOSED: Paper position reconciliation "
                    "failed AND rollback failed"
                )

            raise RuntimeError(
                "FAIL-CLOSED: Paper position reconciliation "
                "failed; paper entry rolled back"
            )

        protection_reconciliation = (
            self.broker.reconcile_protection(
                contract,
                filled_quantity,
            )
        )

        if not protection_reconciliation.get(
            "reconciled"
        ):
            rollback = self.broker.close_position(
                authorization_id,
                contract.get("entry", 0.0),
            )

            if rollback.get("status") != self.broker.CLOSED:
                raise RuntimeError(
                    "FAIL-CLOSED: Paper protection reconciliation "
                    "failed AND rollback failed"
                )

            raise RuntimeError(
                "FAIL-CLOSED: Paper protection reconciliation "
                "failed; paper entry rolled back"
            )

        return {
            "mode": self.PAPER,
            "authorized": True,
            "authorization_id": authorization_id,
            "requested_quantity": requested_quantity,
            "filled_quantity": filled_quantity,
            "remaining_quantity": remaining_quantity,
            "fill_price": float(
                order.get("average_fill_price", 0.0)
            ),
            "order_status": order.get("status"),
            "residual_cancelled": (
                requested_quantity == filled_quantity
                or remaining_quantity == 0.0
            ),
            "order": order,
            "protection": protection,
            "position_reconciliation": position_reconciliation,
            "protection_reconciliation": protection_reconciliation,
        }
