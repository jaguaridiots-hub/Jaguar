"""Production execution-dispatch composition boundary.

This module selects PAPER or LIVE transport composition from the authoritative
execution-mode configuration.

It does not submit broker orders during composition.
In LIVE mode it deliberately provides the dispatch runtime with a fail-closed
PAPER callable rather than constructing any PAPER broker.
"""

from config.config_manager import config
from intelligence.execution_adapter import ExecutionAdapter
from intelligence.live_execution_composition import (
    build_live_execution_runtime,
)
from intelligence.live_execution_dispatch import (
    ExecutionDispatchRuntime,
)
from research import database as db


class ExecutionDispatchCompositionError(RuntimeError):
    """Raised when production execution composition cannot be built safely."""


def _live_paper_executor(_execution):
    raise ExecutionDispatchCompositionError(
        "FAIL-CLOSED: PAPER execution unavailable in LIVE mode"
    )


def _live_paper_authorizer(_execution):
    raise ExecutionDispatchCompositionError(
        "FAIL-CLOSED: PAPER authorization unavailable in LIVE mode"
    )


def _live_paper_rollback(_execution_result):
    raise ExecutionDispatchCompositionError(
        "FAIL-CLOSED: PAPER rollback unavailable in LIVE mode"
    )


def build_execution_dispatch_runtime(*, database_module=db):
    """Build the authoritative PAPER/LIVE dispatch runtime.

    PAPER:
        Instantiates the existing PAPER ExecutionAdapter and delegates to its
        execute() method.

    LIVE:
        Builds the sealed LIVE runtime and supplies only a fail-closed PAPER
        callable to the dispatcher. No PAPER broker is instantiated.

    The function performs composition only; it does not submit orders.
    """
    try:
        mode = config.get_execution_mode()
    except Exception as exc:
        raise ExecutionDispatchCompositionError(
            "FAIL-CLOSED: unable to resolve execution mode"
        ) from exc

    if mode == ExecutionDispatchRuntime.PAPER:
        try:
            paper_adapter = ExecutionAdapter("PAPER")
        except Exception as exc:
            raise ExecutionDispatchCompositionError(
                "FAIL-CLOSED: unable to compose PAPER execution"
            ) from exc

        runtime = ExecutionDispatchRuntime(
            paper_executor=paper_adapter.execute,
            live_runtime=_live_unavailable_runtime(),
        )
        runtime.paper_authorizer = paper_adapter.authorize
        runtime.paper_rollback = paper_adapter.rollback
        return runtime

    if mode == ExecutionDispatchRuntime.LIVE:
        try:
            live_runtime = build_live_execution_runtime(
                database_module=database_module,
            )
        except Exception as exc:
            raise ExecutionDispatchCompositionError(
                "FAIL-CLOSED: unable to compose LIVE execution"
            ) from exc

        runtime = ExecutionDispatchRuntime(
            paper_executor=_live_paper_executor,
            live_runtime=live_runtime,
        )
        runtime.paper_authorizer = _live_paper_authorizer
        runtime.paper_rollback = _live_paper_rollback
        return runtime

    raise ExecutionDispatchCompositionError(
        "FAIL-CLOSED: unsupported execution mode"
    )


class _LiveUnavailableRuntime:
    """Construction-time placeholder; LIVE submission is never routed here."""

    def submit_live(self, *_args, **_kwargs):
        raise ExecutionDispatchCompositionError(
            "FAIL-CLOSED: LIVE runtime unavailable in PAPER composition"
        )


def _live_unavailable_runtime():
    return _LiveUnavailableRuntime()
