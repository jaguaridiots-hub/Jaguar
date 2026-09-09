"""Isolated D2.4 LIVE execution runtime composition boundary.

This module composes the sealed D2.1 coordinator, D2.2 recovery
service, and D2.3 activation barrier.

It does not instantiate a broker, create network transports, submit
orders, or modify production execution wiring.
"""


class LiveExecutionRuntimeError(RuntimeError):
    """Raised when the LIVE runtime composition contract is invalid."""


class LiveExecutionRuntimeBoundary:
    """Explicit dependency-injection boundary for future LIVE runtime use."""

    def __init__(
        self,
        broker,
        *,
        coordinator,
        recovery_service,
        activation_barrier,
    ):
        if broker is None:
            raise LiveExecutionRuntimeError(
                "FAIL-CLOSED: explicit LIVE broker is required"
            )

        if str(
            getattr(broker, "EXECUTION_MODE", "")
        ).strip().upper() != "LIVE":
            raise LiveExecutionRuntimeError(
                "FAIL-CLOSED: runtime requires an explicit LIVE broker"
            )

        if not callable(
            getattr(coordinator, "start_submission", None)
        ):
            raise LiveExecutionRuntimeError(
                "FAIL-CLOSED: invalid execution coordinator"
            )

        if not callable(
            getattr(coordinator, "recover_submission", None)
        ):
            raise LiveExecutionRuntimeError(
                "FAIL-CLOSED: execution coordinator recovery API unavailable"
            )

        if not callable(
            getattr(
                recovery_service,
                "recover_all_non_terminal_submissions",
                None,
            )
        ):
            raise LiveExecutionRuntimeError(
                "FAIL-CLOSED: invalid recovery service"
            )

        if not callable(
            getattr(activation_barrier, "evaluate", None)
        ):
            raise LiveExecutionRuntimeError(
                "FAIL-CLOSED: invalid activation barrier"
            )

        self.broker = broker
        self.coordinator = coordinator
        self.recovery_service = recovery_service
        self.activation_barrier = activation_barrier

    def recover_unresolved(self):
        """Delegate unresolved-submission recovery to the sealed D2.2 service."""
        return self.recovery_service.recover_all_non_terminal_submissions()

    def evaluate_activation(
        self,
        execution,
        market_metadata,
        *,
        activation_requested=False,
    ):
        """Delegate activation evaluation to the sealed D2.3 barrier."""
        return self.activation_barrier.evaluate(
            execution,
            market_metadata,
            self.broker,
            activation_requested=activation_requested,
        )
