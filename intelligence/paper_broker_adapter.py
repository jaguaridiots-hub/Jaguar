"""
Jaguar Quant X
Paper Broker Adapter

Offline broker-shaped execution layer.
No network access.
No exchange credentials.
No live order submission.
"""

import uuid


class PaperBrokerAdapter:

    OPEN = "OPEN"
    FILLED = "FILLED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    CLOSED = "CLOSED"

    def __init__(self):
        self.orders = {}
        self.positions = {}
        self.protections = {}

    def submit_entry(self, execution, fill_quantity=None):
        if not isinstance(execution, dict):
            return {
                "status": self.REJECTED,
                "reason": "Invalid execution contract",
            }

        authorization_id = execution.get("authorization_id")

        if not authorization_id:
            return {
                "status": self.REJECTED,
                "reason": "Missing authorization_id",
            }

        if authorization_id in self.orders:
            return {
                "status": self.REJECTED,
                "reason": "Duplicate authorization_id",
                "authorization_id": authorization_id,
            }

        decision = execution.get("decision")

        if decision not in (
            "ENTER_LONG",
            "ENTER_SHORT",
        ):
            return {
                "status": self.REJECTED,
                "reason": "Non-executable decision",
                "authorization_id": authorization_id,
            }

        quantity = float(
            execution.get("position_size", 0.0) or 0.0
        )

        if quantity <= 0:
            return {
                "status": self.REJECTED,
                "reason": "Invalid position size",
                "authorization_id": authorization_id,
            }

        client_order_id = execution.get("client_order_id")

        if not client_order_id:
            return {
                "status": self.REJECTED,
                "reason": "Missing client_order_id",
                "authorization_id": authorization_id,
            }

        side = (
            "BUY"
            if decision == "ENTER_LONG"
            else "SELL"
        )

        if fill_quantity is None:
            filled_quantity = quantity
        else:
            filled_quantity = float(fill_quantity)

        if filled_quantity <= 0 or filled_quantity > quantity:
            return {
                "status": self.REJECTED,
                "reason": "Invalid fill quantity",
                "authorization_id": authorization_id,
            }

        order_status = (
            self.FILLED
            if filled_quantity == quantity
            else "PARTIALLY_FILLED"
        )

        order = {
            "authorization_id": authorization_id,
            "client_order_id": client_order_id,
            "broker_order_id": "PAPER-" + uuid.uuid4().hex,
            "symbol": execution.get("symbol"),
            "side": side,
            "requested_qty": quantity,
            "filled_qty": filled_quantity,
            "remaining_qty": quantity - filled_quantity,
            "average_fill_price": float(
                execution.get("entry", 0.0)
            ),
            "status": order_status,
        }

        self.orders[authorization_id] = order

        if filled_quantity > 0:
            self.positions[authorization_id] = {
                "authorization_id": authorization_id,
                "symbol": order["symbol"],
                "side": side,
                "quantity": filled_quantity,
                "entry_price": order["average_fill_price"],
                "status": self.OPEN,
            }

        return dict(order)

    def cancel_entry(self, authorization_id):
        order = self.orders.get(authorization_id)

        if order is None:
            return {
                "status": self.REJECTED,
                "reason": "Order not found",
                "authorization_id": authorization_id,
            }

        if order.get("status") == self.CLOSED:
            return {
                "status": self.REJECTED,
                "reason": "Order already closed",
                "authorization_id": authorization_id,
            }

        remaining_quantity = float(
            order.get("remaining_qty", 0.0)
        )

        if remaining_quantity <= 0:
            return {
                "status": self.REJECTED,
                "reason": "No remaining quantity to cancel",
                "authorization_id": authorization_id,
            }

        order = dict(order)
        order["remaining_qty"] = 0.0
        order["status"] = self.CANCELLED

        self.orders[authorization_id] = order

        return dict(order)

    def get_order(self, authorization_id):
        order = self.orders.get(authorization_id)

        return dict(order) if order else None

    def get_position(self, authorization_id):
        position = self.positions.get(authorization_id)

        return dict(position) if position else None

    def submit_protection(self, execution, filled_quantity):
        if not isinstance(execution, dict):
            return {
                "status": self.REJECTED,
                "reason": "Invalid execution contract",
            }

        authorization_id = execution.get("authorization_id")

        if not authorization_id:
            return {
                "status": self.REJECTED,
                "reason": "Missing authorization_id",
            }

        if authorization_id in self.protections:
            return {
                "status": self.REJECTED,
                "reason": "Duplicate protection",
                "authorization_id": authorization_id,
            }

        try:
            filled_quantity = float(filled_quantity)
        except (TypeError, ValueError):
            filled_quantity = 0.0

        if filled_quantity <= 0:
            return {
                "status": self.REJECTED,
                "reason": "Invalid filled quantity",
                "authorization_id": authorization_id,
            }

        stop_loss = execution.get("stop_loss")
        targets = execution.get("targets", [])

        try:
            stop_loss = float(stop_loss)
        except (TypeError, ValueError):
            stop_loss = 0.0

        if stop_loss <= 0:
            return {
                "status": self.REJECTED,
                "reason": "Invalid stop loss",
                "authorization_id": authorization_id,
            }

        if not isinstance(targets, list) or not targets:
            return {
                "status": self.REJECTED,
                "reason": "Missing targets",
                "authorization_id": authorization_id,
            }

        normalized_targets = []

        for target in targets:
            try:
                target = float(target)
            except (TypeError, ValueError):
                target = 0.0

            if target <= 0:
                return {
                    "status": self.REJECTED,
                    "reason": "Invalid target",
                    "authorization_id": authorization_id,
                }

            normalized_targets.append(target)

        decision = execution.get("decision")

        if decision == "ENTER_LONG":
            side = "SELL"
        elif decision == "ENTER_SHORT":
            side = "BUY"
        else:
            return {
                "status": self.REJECTED,
                "reason": "Non-executable decision",
                "authorization_id": authorization_id,
            }

        protection = {
            "authorization_id": authorization_id,
            "side": side,
            "quantity": filled_quantity,
            "stop_loss": stop_loss,
            "targets": normalized_targets,
            "status": self.OPEN,
        }

        self.protections[authorization_id] = protection

        return dict(protection)

    def reconcile_protection(self, execution, filled_quantity):
        if not isinstance(execution, dict):
            return {
                "status": self.REJECTED,
                "reason": "Invalid execution contract",
                "reconciled": False,
            }

        authorization_id = execution.get("authorization_id")
        protection = self.protections.get(authorization_id)

        if protection is None:
            return {
                "status": self.REJECTED,
                "reason": "Protection not found",
                "authorization_id": authorization_id,
                "reconciled": False,
            }

        try:
            expected_quantity = float(filled_quantity)
            expected_stop = float(execution.get("stop_loss", 0.0))
        except (TypeError, ValueError):
            return {
                "status": self.REJECTED,
                "reason": "Invalid protection contract",
                "authorization_id": authorization_id,
                "reconciled": False,
            }

        expected_targets = execution.get("targets", [])

        actual_quantity = float(
            protection.get("quantity", 0.0)
        )
        actual_stop = float(
            protection.get("stop_loss", 0.0)
        )
        actual_targets = protection.get("targets", [])

        if actual_quantity != expected_quantity:
            return {
                "status": self.REJECTED,
                "reason": "Protection quantity mismatch",
                "authorization_id": authorization_id,
                "reconciled": False,
            }

        if actual_stop != expected_stop:
            return {
                "status": self.REJECTED,
                "reason": "Protection stop mismatch",
                "authorization_id": authorization_id,
                "reconciled": False,
            }

        if actual_targets != expected_targets:
            return {
                "status": self.REJECTED,
                "reason": "Protection targets mismatch",
                "authorization_id": authorization_id,
                "reconciled": False,
            }

        return {
            "status": self.OPEN,
            "authorization_id": authorization_id,
            "reconciled": True,
        }

    def reconcile(self, authorization_id, expected_quantity):
        position = self.get_position(authorization_id)

        if position is None:
            return {
                "status": self.REJECTED,
                "reason": "Broker position not found",
                "authorization_id": authorization_id,
                "reconciled": False,
            }

        expected_quantity = float(expected_quantity)

        actual_quantity = float(
            position.get("quantity", 0.0)
        )

        if actual_quantity != expected_quantity:
            return {
                "status": self.REJECTED,
                "reason": "Position quantity mismatch",
                "authorization_id": authorization_id,
                "expected_quantity": expected_quantity,
                "actual_quantity": actual_quantity,
                "reconciled": False,
            }

        return {
            "status": self.OPEN,
            "authorization_id": authorization_id,
            "expected_quantity": expected_quantity,
            "actual_quantity": actual_quantity,
            "reconciled": True,
        }

    def close_position(self, authorization_id, price):
        position = self.positions.get(authorization_id)

        if position is None:
            return {
                "status": self.REJECTED,
                "reason": "Position not found",
                "authorization_id": authorization_id,
            }

        position = dict(position)
        position["exit_price"] = float(price)
        position["status"] = self.CLOSED

        self.positions.pop(authorization_id, None)
        self.protections.pop(authorization_id, None)

        order = self.orders.get(authorization_id)

        if order:
            order = dict(order)
            order["status"] = self.CLOSED
            self.orders[authorization_id] = order

        return position
