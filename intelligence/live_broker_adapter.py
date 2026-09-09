"""
Jaguar Quant X
Upstox Live Broker Adapter

LIVE broker boundary.

This component is intentionally NOT wired into ExecutionAdapter yet.
It performs no database persistence and provides no implicit fallback
to the paper broker.
"""

import math

from market.upstox_order_transport import (
    UpstoxOrderTransport,
    UpstoxOrderTransportError,
)


class LiveBrokerAdapterError(RuntimeError):
    """Raised when the live broker contract cannot be satisfied."""


class LiveBrokerAdapter:
    EXECUTION_MODE = "LIVE"
    BROKER_NAME = "Upstox"

    FILLED = "FILLED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    SUBMITTED = "SUBMITTED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"

    ALLOWED_PRODUCTS = {"I", "D", "MTF"}
    ALLOWED_VALIDITY = {"DAY", "IOC"}
    ALLOWED_ORDER_TYPES = {
        "MARKET",
        "LIMIT",
        "SL",
        "SL-M",
    }

    def __init__(self, transport=None):
        self._transport = (
            transport
            if transport is not None
            else UpstoxOrderTransport()
        )

    @staticmethod
    def _required_string(contract, field):
        value = contract.get(field)

        if not isinstance(value, str):
            raise LiveBrokerAdapterError(
                f"Invalid live execution field: {field}"
            )

        value = value.strip()

        if not value:
            raise LiveBrokerAdapterError(
                f"Missing live execution field: {field}"
            )

        return value

    @staticmethod
    def _positive_finite_number(value, field):
        if isinstance(value, bool):
            raise LiveBrokerAdapterError(
                f"Invalid live execution field: {field}"
            )

        try:
            value = float(value)
        except (TypeError, ValueError) as exc:
            raise LiveBrokerAdapterError(
                f"Invalid live execution field: {field}"
            ) from exc

        if not math.isfinite(value) or value <= 0:
            raise LiveBrokerAdapterError(
                f"Invalid live execution field: {field}"
            )

        return value

    @staticmethod
    def _strict_int(value, field):
        if isinstance(value, bool):
            raise LiveBrokerAdapterError(
                f"Invalid LIVE {field}"
            )

        try:
            normalized = int(value)
        except (TypeError, ValueError) as exc:
            raise LiveBrokerAdapterError(
                f"Invalid LIVE {field}"
            ) from exc

        if str(value).strip() != str(normalized):
            try:
                if float(value) != float(normalized):
                    raise LiveBrokerAdapterError(
                        f"Invalid LIVE {field}"
                    )
            except (TypeError, ValueError):
                raise LiveBrokerAdapterError(
                    f"Invalid LIVE {field}"
                )

        return normalized

    @classmethod
    def _quantity(cls, contract):
        value = cls._positive_finite_number(
            contract.get("position_size"),
            "position_size",
        )

        if not value.is_integer():
            raise LiveBrokerAdapterError(
                "LIVE quantity must be an integer"
            )

        quantity = int(value)

        if quantity <= 0:
            raise LiveBrokerAdapterError(
                "LIVE quantity must be positive"
            )

        return quantity

    @classmethod
    def _price(cls, contract, order_type):
        value = contract.get("entry")

        if order_type == "MARKET":
            if value is None:
                return 0.0

            try:
                value = float(value)
            except (TypeError, ValueError) as exc:
                raise LiveBrokerAdapterError(
                    "Invalid live execution field: entry"
                ) from exc

            if not math.isfinite(value) or value < 0:
                raise LiveBrokerAdapterError(
                    "Invalid live execution field: entry"
                )

            return value

        return cls._positive_finite_number(
            value,
            "entry",
        )

    @staticmethod
    def _strict_bool(value, field):
        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            normalized = value.strip().lower()

            if normalized == "true":
                return True

            if normalized == "false":
                return False

        raise LiveBrokerAdapterError(
            f"Invalid LIVE {field}"
        )

    @classmethod
    def _transaction_type(cls, decision):
        decision = str(decision).upper().strip()

        if decision == "ENTER_LONG":
            return "BUY"

        if decision == "ENTER_SHORT":
            return "SELL"

        raise LiveBrokerAdapterError(
            "LIVE decision must be ENTER_LONG or ENTER_SHORT"
        )

    @classmethod
    def _tag(cls, client_order_id):
        tag = cls._required_string(
            {"client_order_id": client_order_id},
            "client_order_id",
        )

        if len(tag) > 40:
            raise LiveBrokerAdapterError(
                "LIVE client_order_id exceeds Upstox tag limit"
            )

        return tag

    @classmethod
    def build_order_payload(cls, execution):
        if not isinstance(execution, dict):
            raise LiveBrokerAdapterError(
                "Invalid live execution contract"
            )

        mode = str(
            execution.get("mode", "")
        ).upper().strip()

        if mode != cls.EXECUTION_MODE:
            raise LiveBrokerAdapterError(
                "LIVE broker requires mode=LIVE"
            )

        authorization_id = cls._required_string(
            execution,
            "authorization_id",
        )

        client_order_id = cls._required_string(
            execution,
            "client_order_id",
        )

        instrument_token = cls._required_string(
            execution,
            "instrument_token",
        )

        decision = cls._required_string(
            execution,
            "decision",
        )

        product = str(
            execution.get("product", "")
        ).upper().strip()

        if product not in cls.ALLOWED_PRODUCTS:
            raise LiveBrokerAdapterError(
                "Invalid LIVE product"
            )

        validity = str(
            execution.get("validity", "DAY")
        ).upper().strip()

        if validity not in cls.ALLOWED_VALIDITY:
            raise LiveBrokerAdapterError(
                "Invalid LIVE validity"
            )

        order_type = str(
            execution.get("order_type", "MARKET")
        ).upper().strip()

        if order_type not in cls.ALLOWED_ORDER_TYPES:
            raise LiveBrokerAdapterError(
                "Invalid LIVE order_type"
            )

        quantity = cls._quantity(execution)
        transaction_type = cls._transaction_type(decision)
        price = cls._price(
            execution,
            order_type,
        )

        trigger_price = execution.get(
            "trigger_price",
            0,
        )

        try:
            trigger_price = float(trigger_price)
        except (TypeError, ValueError) as exc:
            raise LiveBrokerAdapterError(
                "Invalid LIVE trigger_price"
            ) from exc

        if not math.isfinite(trigger_price) or trigger_price < 0:
            raise LiveBrokerAdapterError(
                "Invalid LIVE trigger_price"
            )

        if order_type in {"SL", "SL-M"} and trigger_price <= 0:
            raise LiveBrokerAdapterError(
                "LIVE stop orders require positive trigger_price"
            )

        try:
            market_protection = cls._strict_int(
                execution.get("market_protection", -1),
                "market_protection",
            )
        except LiveBrokerAdapterError:
            raise

        if market_protection < -1 or market_protection > 25:
            raise LiveBrokerAdapterError(
                "Invalid LIVE market_protection"
            )

        if market_protection == 0 and order_type in {
            "MARKET",
            "SL-M",
        }:
            raise LiveBrokerAdapterError(
                "LIVE market_protection=0 is invalid for market orders"
            )

        return {
            "quantity": quantity,
            "product": product,
            "validity": validity,
            "price": price,
            "tag": cls._tag(client_order_id),
            "instrument_token": instrument_token,
            "order_type": order_type,
            "transaction_type": transaction_type,
            "disclosed_quantity": 0,
            "trigger_price": trigger_price,
            "is_amo": cls._strict_bool(
                execution.get("is_amo", False),
                "is_amo",
            ),
            "slice": cls._strict_bool(
                execution.get("slice", False),
                "slice",
            ),
            "market_protection": market_protection,
        }

    @classmethod
    def _normalize_status(cls, status):
        status = str(status or "").upper().strip()

        if status in {
            "COMPLETE",
            "COMPLETED",
            "FILLED",
        }:
            return cls.FILLED

        if status in {
            "REJECTED",
            "REJECT",
        }:
            return cls.REJECTED

        if status in {
            "CANCELLED",
            "CANCELED",
        }:
            return cls.CANCELLED

        return cls.SUBMITTED

    @staticmethod
    def _response_data(payload):
        if not isinstance(payload, dict):
            raise LiveBrokerAdapterError(
                "Malformed Upstox response"
            )

        if payload.get("status") != "success":
            raise LiveBrokerAdapterError(
                "Upstox operation was not successful"
            )

        data = payload.get("data")

        if not isinstance(data, (dict, list)):
            raise LiveBrokerAdapterError(
                "Malformed Upstox response data"
            )

        return data

    @classmethod
    def _order_result(
        cls,
        *,
        execution,
        broker_order_id,
        status,
        requested_qty,
        filled_qty=0,
        pending_qty=0,
        average_price=0.0,
        instrument_token=None,
        transaction_type=None,
        tag=None,
        raw_status=None,
    ):
        if not broker_order_id:
            raise LiveBrokerAdapterError(
                "Upstox response missing order identity"
            )

        return {
            "authorization_id": execution[
                "authorization_id"
            ],
            "client_order_id": execution[
                "client_order_id"
            ],
            "broker_order_id": str(
                broker_order_id
            ),
            "symbol": execution.get("symbol"),
            "instrument_token": (
                instrument_token
                or execution.get("instrument_token")
            ),
            "side": (
                transaction_type
                or cls._transaction_type(
                    execution["decision"]
                )
            ),
            "requested_qty": requested_qty,
            "filled_qty": filled_qty,
            "remaining_qty": pending_qty,
            "average_fill_price": average_price,
            "status": status,
            "raw_status": raw_status,
            "tag": tag,
        }

    def submit_entry(self, execution):
        payload = self.build_order_payload(
            execution
        )

        try:
            response = self._transport.place_order(
                payload
            )
        except UpstoxOrderTransportError as exc:
            raise LiveBrokerAdapterError(
                "LIVE order placement failed"
            ) from exc

        data = self._response_data(response)

        order_ids = data.get("order_ids")

        if not isinstance(order_ids, list) or not order_ids:
            raise LiveBrokerAdapterError(
                "Upstox placement response missing order_ids"
            )

        if any(
            not isinstance(order_id, str)
            or not order_id.strip()
            for order_id in order_ids
        ):
            raise LiveBrokerAdapterError(
                "Upstox returned invalid order identity"
            )

        # A single Jaguar execution can produce multiple broker
        # orders when Upstox slicing is enabled. Do not silently
        # pretend that there is one order.
        if len(order_ids) != 1:
            raise LiveBrokerAdapterError(
                "LIVE execution received multiple broker order IDs; "
                "explicit sliced-order reconciliation is required"
            )

        broker_order_id = order_ids[0]

        return self._order_result(
            execution=execution,
            broker_order_id=broker_order_id,
            status=self.SUBMITTED,
            requested_qty=payload["quantity"],
            instrument_token=payload[
                "instrument_token"
            ],
            transaction_type=payload[
                "transaction_type"
            ],
            tag=payload["tag"],
        )

    def cancel_entry(self, broker_order_id):
        broker_order_id = self._required_string(
            {"broker_order_id": broker_order_id},
            "broker_order_id",
        )

        try:
            response = self._transport.cancel_order(
                broker_order_id
            )
        except UpstoxOrderTransportError as exc:
            raise LiveBrokerAdapterError(
                "LIVE order cancellation failed"
            ) from exc

        data = self._response_data(response)

        returned_order_id = str(
            data.get("order_id", "")
        ).strip()

        if returned_order_id != broker_order_id:
            raise LiveBrokerAdapterError(
                "Upstox cancellation identity mismatch"
            )

        return {
            "broker_order_id": broker_order_id,
            "status": self.CANCELLED,
        }

    def get_order(self, broker_order_id):
        broker_order_id = self._required_string(
            {"broker_order_id": broker_order_id},
            "broker_order_id",
        )

        try:
            response = (
                self._transport.get_order_details(
                    broker_order_id
                )
            )
        except UpstoxOrderTransportError as exc:
            raise LiveBrokerAdapterError(
                "LIVE order lookup failed"
            ) from exc

        data = self._response_data(response)

        returned_order_id = str(
            data.get("order_id", "")
        ).strip()

        if returned_order_id != broker_order_id:
            raise LiveBrokerAdapterError(
                "Upstox order identity mismatch"
            )

        try:
            requested_qty = int(
                data.get("quantity", 0)
            )
            filled_qty = int(
                data.get("filled_quantity", 0)
            )
            pending_qty = int(
                data.get("pending_quantity", 0)
            )
        except (TypeError, ValueError) as exc:
            raise LiveBrokerAdapterError(
                "Upstox returned invalid quantity fields"
            ) from exc

        try:
            average_price = float(
                data.get("average_price") or 0.0
            )
        except (TypeError, ValueError) as exc:
            raise LiveBrokerAdapterError(
                "Upstox returned invalid average price"
            ) from exc

        return {
            "broker_order_id": broker_order_id,
            "status": self._normalize_status(
                data.get("status")
            ),
            "raw_status": data.get("status"),
            "requested_qty": requested_qty,
            "filled_qty": filled_qty,
            "remaining_qty": pending_qty,
            "average_fill_price": average_price,
            "instrument_token": data.get(
                "instrument_token"
            ),
            "transaction_type": data.get(
                "transaction_type"
            ),
            "tag": data.get("tag"),
            "exchange_order_id": data.get(
                "exchange_order_id"
            ),
            "status_message": data.get(
                "status_message"
            ),
        }

    def observe_order(self, intent):
        """
        Return one broker observation in the shape required by
        Jaguar ExecutionRecovery.

        The durable intent remains authoritative for Jaguar-side
        identity; the broker response supplies broker state.
        """
        if not isinstance(intent, dict):
            raise LiveBrokerAdapterError(
                "LIVE order observation requires an intent object"
            )

        authorization_id = self._required_string(
            intent,
            "authorization_id",
        )

        client_order_id = self._required_string(
            intent,
            "client_order_id",
        )

        broker_order_id = self._required_string(
            intent,
            "broker_order_id",
        )

        symbol = self._required_string(
            intent,
            "symbol",
        )

        decision = self._required_string(
            intent,
            "decision",
        )

        broker_order = self.get_order(
            broker_order_id
        )

        if broker_order is None:
            return None

        expected_side = self._transaction_type(
            "ENTER_LONG"
            if decision.upper() == "LONG"
            else "ENTER_SHORT"
        )

        observed_token = str(
            broker_order.get(
                "instrument_token",
                "",
            ) or ""
        ).strip()

        expected_token = str(
            intent.get(
                "instrument_token",
                "",
            ) or ""
        ).strip()

        if expected_token and observed_token:
            if observed_token != expected_token:
                raise LiveBrokerAdapterError(
                    "LIVE broker instrument identity mismatch"
                )

        observed_side = str(
            broker_order.get(
                "transaction_type",
                "",
            ) or ""
        ).upper().strip()

        if observed_side and observed_side != expected_side:
            raise LiveBrokerAdapterError(
                "LIVE broker side identity mismatch"
            )

        observed_tag = str(
            broker_order.get(
                "tag",
                "",
            ) or ""
        ).strip()

        if observed_tag and observed_tag != client_order_id:
            raise LiveBrokerAdapterError(
                "LIVE broker client order identity mismatch"
            )

        normalized = dict(broker_order)
        normalized.update({
            "authorization_id": authorization_id,
            "client_order_id": client_order_id,
            "broker_order_id": broker_order_id,
            "symbol": symbol,
            "side": expected_side,
        })

        return normalized

    def get_order_history(
        self,
        *,
        broker_order_id=None,
        client_order_id=None,
    ):
        if broker_order_id is None and client_order_id is None:
            raise LiveBrokerAdapterError(
                "LIVE order history requires order identity"
            )

        try:
            response = (
                self._transport.get_order_history(
                    order_id=broker_order_id,
                    tag=client_order_id,
                )
            )
        except UpstoxOrderTransportError as exc:
            raise LiveBrokerAdapterError(
                "LIVE order history lookup failed"
            ) from exc

        data = self._response_data(response)

        if not isinstance(data, list):
            data = [data]

        return data

    def get_positions(self):
        try:
            response = self._transport.get_positions()
        except UpstoxOrderTransportError as exc:
            raise LiveBrokerAdapterError(
                "LIVE positions lookup failed"
            ) from exc

        data = self._response_data(response)

        if not isinstance(data, list):
            raise LiveBrokerAdapterError(
                "Upstox positions response must be a list"
            )

        return data

    def get_position(
        self,
        instrument_token,
    ):
        instrument_token = self._required_string(
            {"instrument_token": instrument_token},
            "instrument_token",
        )

        positions = self.get_positions()

        matches = [
            dict(position)
            for position in positions
            if str(
                position.get("instrument_token", "")
            ).strip() == instrument_token
        ]

        if len(matches) > 1:
            raise LiveBrokerAdapterError(
                "Multiple Upstox positions matched instrument"
            )

        return matches[0] if matches else None

    def observe_position(
        self,
        intent,
        *,
        instrument_token=None,
    ):
        """
        Return one normalized broker-position observation for Jaguar
        ExecutionRecovery.

        Jaguar-side identity is taken from the durable intent.
        Broker-side position identity comes from instrument_token.
        This method is read-only and never mutates broker state.
        """
        if not isinstance(intent, dict):
            raise LiveBrokerAdapterError(
                "LIVE position observation requires an intent object"
            )

        authorization_id = self._required_string(
            intent,
            "authorization_id",
        )

        symbol = self._required_string(
            intent,
            "symbol",
        )

        resolved_token = (
            instrument_token
            or intent.get("instrument_token")
        )

        resolved_token = self._required_string(
            {"instrument_token": resolved_token},
            "instrument_token",
        )

        position = self.get_position(
            resolved_token
        )

        if position is None:
            return None

        observed_token = str(
            position.get("instrument_token", "")
        ).strip()

        if observed_token != resolved_token:
            raise LiveBrokerAdapterError(
                "LIVE broker position instrument identity mismatch"
            )

        quantity = position.get("quantity")

        try:
            quantity = float(quantity)
        except (TypeError, ValueError) as exc:
            raise LiveBrokerAdapterError(
                "LIVE broker position quantity is invalid"
            ) from exc

        if not math.isfinite(quantity):
            raise LiveBrokerAdapterError(
                "LIVE broker position quantity is invalid"
            )

        normalized = dict(position)
        normalized.update({
            "authorization_id": authorization_id,
            "symbol": symbol,
            "instrument_token": resolved_token,
            "quantity": quantity,
        })

        return normalized

    def observe_protection(
        self,
        intent,
        protection,
        *,
        instrument_token=None,
    ):
        """
        Return one normalized broker-protection observation.

        Read-only. No broker mutation occurs.
        """
        if not isinstance(intent, dict):
            raise LiveBrokerAdapterError(
                "LIVE protection observation requires an intent object"
            )

        if not isinstance(protection, dict):
            raise LiveBrokerAdapterError(
                "LIVE protection observation requires a protection object"
            )

        authorization_id = self._required_string(
            intent,
            "authorization_id",
        )

        symbol = self._required_string(
            intent,
            "symbol",
        )

        resolved_token = (
            instrument_token
            or intent.get("instrument_token")
        )

        resolved_token = self._required_string(
            {"instrument_token": resolved_token},
            "instrument_token",
        )

        broker_order_id = self._required_string(
            protection,
            "broker_order_id",
        )

        order = self.get_order(
            broker_order_id,
        )

        if order is None:
            return None

        if not isinstance(order, dict):
            raise LiveBrokerAdapterError(
                "LIVE protection order observation must be an object"
            )

        observed_order_id = (
            order.get("broker_order_id")
            or order.get("order_id")
        )

        observed_order_id = self._required_string(
            {"broker_order_id": observed_order_id},
            "broker_order_id",
        )

        if observed_order_id != broker_order_id:
            raise LiveBrokerAdapterError(
                "LIVE protection broker_order_id mismatch"
            )

        observed_token = self._required_string(
            {
                "instrument_token": order.get(
                    "instrument_token"
                )
            },
            "instrument_token",
        )

        if observed_token != resolved_token:
            raise LiveBrokerAdapterError(
                "LIVE protection instrument identity mismatch"
            )

        quantity = self._positive_finite_number(
            order.get("quantity"),
            "protection_quantity",
        )

        status = self._required_string(
            {
                "status": order.get("status")
            },
            "status",
        ).upper()

        order_type = self._required_string(
            {
                "order_type": order.get("order_type")
            },
            "order_type",
        ).upper()

        transaction_type = self._required_string(
            {
                "transaction_type": order.get(
                    "transaction_type"
                )
            },
            "transaction_type",
        ).upper()

        trigger_price = order.get("trigger_price")
        if trigger_price is not None:
            try:
                trigger_price = float(trigger_price)
            except (TypeError, ValueError) as exc:
                raise LiveBrokerAdapterError(
                    "LIVE protection trigger_price is invalid"
                ) from exc

            if not math.isfinite(trigger_price) or trigger_price < 0:
                raise LiveBrokerAdapterError(
                    "LIVE protection trigger_price is invalid"
                )

        price = order.get("price")
        if price is not None:
            try:
                price = float(price)
            except (TypeError, ValueError) as exc:
                raise LiveBrokerAdapterError(
                    "LIVE protection price is invalid"
                ) from exc

            if not math.isfinite(price) or price < 0:
                raise LiveBrokerAdapterError(
                    "LIVE protection price is invalid"
                )

        normalized = dict(order)
        normalized.update(
            {
                "authorization_id": authorization_id,
                "symbol": symbol,
                "instrument_token": resolved_token,
                "broker_order_id": observed_order_id,
                "quantity": quantity,
                "status": status,
                "order_type": order_type,
                "transaction_type": transaction_type,
                "trigger_price": trigger_price,
                "price": price,
            }
        )

        return normalized

    def close_position(self, *args, **kwargs):
        raise LiveBrokerAdapterError(
            "FAIL-CLOSED: LIVE position close is not enabled"
        )
