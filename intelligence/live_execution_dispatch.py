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
        live_executor,
        live_runtime,
    ):
        if not callable(paper_executor):
            raise LiveExecutionDispatchError(
                "FAIL-CLOSED: paper executor is required"
            )

        if not callable(live_executor):
            raise LiveExecutionDispatchError(
                "FAIL-CLOSED: LIVE executor is required"
            )

        if live_runtime is None:
            raise LiveExecutionDispatchError(
                "FAIL-CLOSED: LIVE runtime is required"
            )

        if not callable(
            getattr(live_runtime, "recover_unresolved", None)
        ):
            raise LiveExecutionDispatchError(
                "FAIL-CLOSED: LIVE runtime recovery API unavailable"
            )

        if not callable(
            getattr(live_runtime, "evaluate_activation", None)
        ):
            raise LiveExecutionDispatchError(
                "FAIL-CLOSED: LIVE runtime activation API unavailable"
            )

        self.paper_executor = paper_executor
        self.live_executor = live_executor
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

        recovery = self.live_runtime.recover_unresolved()

        if recovery is None:
            recovery = []

        if not isinstance(recovery, (list, tuple)):
            raise LiveExecutionDispatchError(
                "FAIL-CLOSED: invalid LIVE recovery result"
            )

        if recovery:
            raise LiveExecutionDispatchError(
                "FAIL-CLOSED: LIVE execution blocked by unresolved recovery"
            )

        activation = self.live_runtime.evaluate_activation(
            execution,
            market_metadata,
            activation_requested=True,
        )

        if not isinstance(activation, dict):
            raise LiveExecutionDispatchError(
                "FAIL-CLOSED: invalid LIVE activation result"
            )

        if (
            activation.get("allowed") is not True
            or activation.get("status") != "ALLOW"
            or activation.get("gate") != "LIVE_ACTIVATION"
        ):
            raise LiveExecutionDispatchError(
                "FAIL-CLOSED: LIVE activation denied"
            )

        return self.live_executor(execution)
