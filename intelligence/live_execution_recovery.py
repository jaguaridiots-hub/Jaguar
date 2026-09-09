"""Isolated Jaguar V10 live submission recovery orchestration.

D2.2 boundary:
- enumerate durable non-terminal submission journals;
- invoke the sealed D2.1 coordinator recovery primitive once per journal;
- preserve database ordering and coordinator results;
- perform no broker submission or direct journal mutation.

This module is intentionally not wired into main.py, ExecutionAdapter,
execution_gateway_v2.py, or live authorization.
"""

from intelligence.live_execution_coordinator import (
    LiveExecutionCoordinator,
    LiveExecutionCoordinatorError,
)
from research import database as db


class LiveExecutionRecoveryError(RuntimeError):
    """Raised when batch recovery cannot be safely orchestrated."""


class LiveExecutionRecoveryService:
    """Batch orchestration boundary for unresolved live submissions."""

    def __init__(
        self,
        broker=None,
        *,
        database_module=db,
        coordinator=None,
    ):
        if coordinator is None:
            if broker is None:
                raise LiveExecutionRecoveryError(
                    "FAIL-CLOSED: broker is required when coordinator is not supplied"
                )
            try:
                coordinator = LiveExecutionCoordinator(
                    broker,
                    database_module=database_module,
                )
            except Exception as exc:
                raise LiveExecutionRecoveryError(
                    "FAIL-CLOSED: unable to initialize live recovery coordinator"
                ) from exc

        if not hasattr(coordinator, "recover_submission") or not callable(
            coordinator.recover_submission
        ):
            raise LiveExecutionRecoveryError(
                "FAIL-CLOSED: invalid recovery coordinator"
            )

        if not hasattr(database_module, "list_non_terminal_execution_submissions"):
            raise LiveExecutionRecoveryError(
                "FAIL-CLOSED: database recovery enumeration API is unavailable"
            )

        self.db = database_module
        self.coordinator = coordinator

    def recover_all_non_terminal_submissions(self):
        """Recover every durable non-terminal submission in DB order.

        The coordinator remains the sole owner of per-submission recovery
        semantics. This method performs enumeration and delegation only.
        """
        rows = self.db.list_non_terminal_execution_submissions()

        if rows is None:
            rows = []

        if not isinstance(rows, (list, tuple)):
            raise LiveExecutionRecoveryError(
                "FAIL-CLOSED: non-terminal submission enumeration must return a sequence"
            )

        results = []

        for row in rows:
            try:
                journal = dict(row)
            except Exception as exc:
                raise LiveExecutionRecoveryError(
                    "FAIL-CLOSED: invalid execution submission journal row"
                ) from exc

            authorization_id = journal.get("authorization_id")

            if (
                not isinstance(authorization_id, str)
                or not authorization_id.strip()
            ):
                raise LiveExecutionRecoveryError(
                    "FAIL-CLOSED: submission journal has invalid authorization_id"
                )

            authorization_id = authorization_id.strip()

            try:
                result = self.coordinator.recover_submission(
                    authorization_id
                )
            except LiveExecutionCoordinatorError:
                raise
            except Exception as exc:
                raise LiveExecutionRecoveryError(
                    "FAIL-CLOSED: unexpected live submission recovery failure"
                ) from exc

            results.append(result)

        return results
