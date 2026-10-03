"""
Jaguar Quant X
Canonical execution identity boundary.

Transport-neutral identity binding for authorized executions.
This module does not know about brokers, PAPER/LIVE transport,
database persistence, or position state.
"""

import uuid


class ExecutionIdentityError(RuntimeError):
    """Raised when execution identity binding fails closed."""


def bind_execution_identity(execution):
    """
    Return a copy of an authorized execution carrying one durable
    trade_uuid.

    A missing trade_uuid is allocated exactly once.
    A valid existing trade_uuid is preserved.
    Invalid required identities fail closed.
    """
    if not isinstance(execution, dict):
        raise ExecutionIdentityError(
            "FAIL-CLOSED: execution identity requires an object"
        )

    authorization_id = execution.get("authorization_id")
    if not isinstance(authorization_id, str) or not authorization_id.strip():
        raise ExecutionIdentityError(
            "FAIL-CLOSED: execution identity requires authorization_id"
        )

    client_order_id = execution.get("client_order_id")
    if not isinstance(client_order_id, str) or not client_order_id.strip():
        raise ExecutionIdentityError(
            "FAIL-CLOSED: execution identity requires client_order_id"
        )

    result = dict(execution)
    existing = result.get("trade_uuid")

    if existing is None:
        existing = str(uuid.uuid4())
    elif not isinstance(existing, str) or not existing.strip():
        raise ExecutionIdentityError(
            "FAIL-CLOSED: execution contains invalid trade_uuid"
        )
    else:
        existing = existing.strip()

    result["trade_uuid"] = existing
    return result
