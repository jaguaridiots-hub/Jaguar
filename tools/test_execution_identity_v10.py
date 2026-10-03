"""D2.8-B2 canonical execution identity contract tests."""

from pathlib import Path

from intelligence.execution_identity import (
    ExecutionIdentityError,
    bind_execution_identity,
)


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def base_execution():
    return {
        "ready": True,
        "approved": True,
        "status": "EXECUTE",
        "gate": "AUTHORIZED",
        "mode": "PAPER",
        "authorization_id": "AUTH-B2-001",
        "client_order_id": "JQX-B2-CLIENT-001",
        "symbol": "GOLDM",
    }


def test_allocates_once():
    execution = bind_execution_identity(base_execution())

    trade_uuid = execution.get("trade_uuid")

    assert_true(
        isinstance(trade_uuid, str) and trade_uuid.strip(),
        "trade_uuid was not allocated",
    )

    rebound = bind_execution_identity(execution)

    assert_true(
        rebound["trade_uuid"] == trade_uuid,
        "valid existing trade_uuid was replaced",
    )

    print("D28B2_ALLOCATE_ONCE: PASS")


def test_preserves_existing_identity():
    execution = base_execution()
    execution["trade_uuid"] = "TRADE-B2-EXISTING"

    bound = bind_execution_identity(execution)

    assert_true(
        bound["trade_uuid"] == "TRADE-B2-EXISTING",
        "existing trade_uuid was not preserved",
    )

    print("D28B2_PRESERVE_EXISTING: PASS")


def test_returns_copy():
    execution = base_execution()
    bound = bind_execution_identity(execution)

    assert_true(
        bound is not execution,
        "identity binder returned original object",
    )

    print("D28B2_COPY: PASS")


def test_missing_authorization_fails_closed():
    execution = base_execution()
    execution.pop("authorization_id")

    try:
        bind_execution_identity(execution)
    except ExecutionIdentityError as exc:
        assert_true(
            "authorization_id" in str(exc),
            "wrong failure for missing authorization_id",
        )
    else:
        raise AssertionError(
            "missing authorization_id was accepted"
        )

    print("D28B2_AUTHORIZATION_REQUIRED: PASS")


def test_missing_client_order_fails_closed():
    execution = base_execution()
    execution.pop("client_order_id")

    try:
        bind_execution_identity(execution)
    except ExecutionIdentityError as exc:
        assert_true(
            "client_order_id" in str(exc),
            "wrong failure for missing client_order_id",
        )
    else:
        raise AssertionError(
            "missing client_order_id was accepted"
        )

    print("D28B2_CLIENT_ORDER_REQUIRED: PASS")


def test_invalid_existing_identity_fails_closed():
    execution = base_execution()
    execution["trade_uuid"] = ""

    try:
        bind_execution_identity(execution)
    except ExecutionIdentityError as exc:
        assert_true(
            "trade_uuid" in str(exc),
            "wrong failure for invalid trade_uuid",
        )
    else:
        raise AssertionError(
            "invalid trade_uuid was accepted"
        )

    print("D28B2_INVALID_EXISTING_IDENTITY: PASS")


def test_main_wiring_order():
    main_source = Path("main.py").read_text()

    bind = main_source.index(
        "enterprise_execution = bind_execution_identity("
    )
    authorize = main_source.index(
        "paper_authorization = execution_dispatch_runtime.paper_authorizer("
    )
    consume = main_source.index(
        'trade_uuid = execution.get(\n'
    )

    assert_true(
        bind < authorize,
        "identity binding must precede transport-specific authorization",
    )

    assert_true(
        authorize < consume,
        "trade_uuid consumption must occur after authorization",
    )

    assert_true(
        'enterprise["execution"] = enterprise_execution' in main_source,
        "canonical enterprise execution identity was not persisted",
    )

    assert_true(
        "uuid.uuid4" not in main_source,
        "main.py still allocates trade_uuid directly",
    )

    print("D28B2_MAIN_WIRING_ORDER: PASS")


def run():
    test_allocates_once()
    test_preserves_existing_identity()
    test_returns_copy()
    test_main_wiring_order()
    test_missing_authorization_fails_closed()
    test_missing_client_order_fails_closed()
    test_invalid_existing_identity_fails_closed()

    print("D28B2_EXECUTION_IDENTITY: PASS")


if __name__ == "__main__":
    run()
