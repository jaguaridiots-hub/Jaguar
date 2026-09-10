"""Isolated D2.7-A execution dispatch contract.

This module composes execution-mode dispatch only. It does not create
trading authority, instantiate brokers, call broker APIs, or modify
production execution wiring.
"""


class LiveExecutionDispatchError(RuntimeError):
    """Raised when execution dispatch cannot proceed safely."""


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

        return self.live_runtime.submit_live(
            execution,
            market_metadata,
            activation_requested=True,
        )
