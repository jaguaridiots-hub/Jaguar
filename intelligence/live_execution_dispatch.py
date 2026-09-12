"""Isolated D2.7-A execution dispatch contract.

This module composes execution-mode dispatch only. It does not create
trading authority, instantiate brokers, call broker APIs, or modify
production execution wiring.
"""


class LiveExecutionDispatchError(RuntimeError):
    """Raised when execution dispatch cannot proceed safely."""


def normalize_live_execution(execution):
    """Normalize the Jaguar gateway LIVE contract into the D2 canonical contract.

    Gateway:
        ENTER_LONG / ENTER_SHORT + position_size

    D2:
        LONG / SHORT + quantity

    Returns a new dictionary and never mutates the caller's execution object.
    """
    if not isinstance(execution, dict):
        raise LiveExecutionDispatchError(
            "FAIL-CLOSED: invalid LIVE execution contract"
        )

    normalized = dict(execution)

    mode = str(normalized.get("mode", "")).strip().upper()
    if mode != "LIVE":
        raise LiveExecutionDispatchError(
            "FAIL-CLOSED: LIVE normalization requires mode=LIVE"
        )

    decision = str(normalized.get("decision", "")).strip().upper()

    decision_map = {
        "ENTER_LONG": "LONG",
        "ENTER_SHORT": "SHORT",
    }

    if decision in decision_map:
        decision = decision_map[decision]
    elif decision not in {"LONG", "SHORT"}:
        raise LiveExecutionDispatchError(
            "FAIL-CLOSED: invalid LIVE decision"
        )

    raw_position_size = normalized.get("position_size")
    raw_quantity = normalized.get("quantity")

    if raw_position_size is not None and raw_quantity is not None:
        if isinstance(raw_position_size, bool) or isinstance(raw_quantity, bool):
            raise LiveExecutionDispatchError(
                "FAIL-CLOSED: invalid LIVE quantity fields"
            )
        try:
            if float(raw_position_size) != float(raw_quantity):
                raise LiveExecutionDispatchError(
                    "FAIL-CLOSED: conflicting LIVE quantity fields"
                )
        except (TypeError, ValueError):
            raise LiveExecutionDispatchError(
                "FAIL-CLOSED: invalid LIVE quantity fields"
            )

    raw_quantity = (
        raw_quantity
        if raw_quantity is not None
        else raw_position_size
    )

    if raw_quantity is None:
        raise LiveExecutionDispatchError(
            "FAIL-CLOSED: LIVE quantity is required"
        )

    if isinstance(raw_quantity, bool):
        raise LiveExecutionDispatchError(
            "FAIL-CLOSED: LIVE quantity is invalid"
        )

    try:
        quantity = float(raw_quantity)
    except (TypeError, ValueError) as exc:
        raise LiveExecutionDispatchError(
            "FAIL-CLOSED: LIVE quantity is invalid"
        ) from exc

    if quantity != quantity or quantity in {
        float("inf"),
        float("-inf"),
    }:
        raise LiveExecutionDispatchError(
            "FAIL-CLOSED: LIVE quantity is not finite"
        )

    if quantity <= 0 or not quantity.is_integer():
        raise LiveExecutionDispatchError(
            "FAIL-CLOSED: LIVE quantity must be a positive integer"
        )

    normalized["decision"] = decision
    normalized["quantity"] = int(quantity)
    normalized.pop("position_size", None)

    return normalized


class ExecutionDispatchRuntime:
    """Fail-closed mode-aware dispatch boundary."""

    PAPER = "PAPER"
    LIVE = "LIVE"

    def __init__(
        self,
        *,
        paper_executor,
        live_runtime,
    ):
        if not callable(paper_executor):
            raise LiveExecutionDispatchError(
                "FAIL-CLOSED: paper executor is required"
            )

        if live_runtime is None:
            raise LiveExecutionDispatchError(
                "FAIL-CLOSED: LIVE runtime is required"
            )

        if not callable(
            getattr(live_runtime, "submit_live", None)
        ):
            raise LiveExecutionDispatchError(
                "FAIL-CLOSED: LIVE runtime submission API unavailable"
            )

        self.paper_executor = paper_executor
        self.live_runtime = live_runtime

    @staticmethod
    def _mode(execution):
        if not isinstance(execution, dict):
            raise LiveExecutionDispatchError(
                "FAIL-CLOSED: invalid execution contract"
            )

        mode = str(execution.get("mode", "")).strip().upper()

        if mode not in {
            ExecutionDispatchRuntime.PAPER,
            ExecutionDispatchRuntime.LIVE,
        }:
            raise LiveExecutionDispatchError(
                "FAIL-CLOSED: explicit execution mode is required"
            )

        return mode

    def dispatch(
        self,
        execution,
        market_metadata=None,
        *,
        activation_requested=False,
    ):
        mode = self._mode(execution)

        if mode == self.PAPER:
            if activation_requested is True:
                raise LiveExecutionDispatchError(
                    "FAIL-CLOSED: activation request is invalid for PAPER"
                )

            return self.paper_executor(execution)

        if activation_requested is not True:
            raise LiveExecutionDispatchError(
                "FAIL-CLOSED: LIVE execution requires explicit activation"
            )

        normalized_execution = normalize_live_execution(execution)

        return self.live_runtime.submit_live(
            normalized_execution,
            market_metadata,
            activation_requested=True,
        )
