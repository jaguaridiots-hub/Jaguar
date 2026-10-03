"""Explicit LIVE execution composition boundary.

This module composes the sealed LIVE broker, coordinator, recovery,
activation, and runtime boundaries.

It does not submit orders and performs no network I/O during composition
except construction of the authenticated transport/session object.
LIVE mode must be explicitly selected before the composition is built.
"""

from config.config_manager import config
from intelligence.live_broker_adapter import LiveBrokerAdapter
from intelligence.live_execution_activation import (
    LiveExecutionActivationBarrier,
)
from intelligence.live_execution_coordinator import (
    LiveExecutionCoordinator,
)
from intelligence.live_execution_recovery import (
    LiveExecutionRecoveryService,
)
from intelligence.live_execution_runtime import (
    LiveExecutionRuntimeBoundary,
)
from research import database as db


class LiveExecutionCompositionError(RuntimeError):
    """Raised when the LIVE execution composition cannot be built safely."""


def build_live_execution_runtime(*, database_module=db):
    """Build the sealed LIVE submission runtime.

    LIVE mode must be explicitly selected. The composition performs no
    broker submission and no implicit PAPER fallback.
    """

    try:
        mode = config.get_execution_mode()
    except Exception as exc:
        raise LiveExecutionCompositionError(
            "FAIL-CLOSED: unable to resolve execution mode"
        ) from exc

    if mode != "LIVE":
        raise LiveExecutionCompositionError(
            "FAIL-CLOSED: LIVE execution composition requires mode=LIVE"
        )

    if database_module is None:
        raise LiveExecutionCompositionError(
            "FAIL-CLOSED: database module is required"
        )

    try:
        broker = LiveBrokerAdapter()

        coordinator = LiveExecutionCoordinator(
            broker,
            database_module=database_module,
        )

        recovery_service = LiveExecutionRecoveryService(
            coordinator=coordinator,
            database_module=database_module,
        )

        activation_barrier = LiveExecutionActivationBarrier(
            database_module=database_module,
        )

        return LiveExecutionRuntimeBoundary(
            broker,
            coordinator=coordinator,
            recovery_service=recovery_service,
            activation_barrier=activation_barrier,
        )
    except LiveExecutionCompositionError:
        raise
    except Exception as exc:
        raise LiveExecutionCompositionError(
            "FAIL-CLOSED: unable to compose LIVE execution runtime"
        ) from exc
