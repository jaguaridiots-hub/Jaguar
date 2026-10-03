from __future__ import annotations

import hashlib
import inspect
from pathlib import Path
from types import SimpleNamespace

from intelligence.execution_dispatch_composition import (
    build_execution_dispatch_runtime,
)
from intelligence.execution_identity import bind_execution_identity


ROOT = Path(".")
PRODUCTION_FILES = (
    Path("main.py"),
    Path("intelligence/execution_adapter.py"),
    Path("intelligence/execution_dispatch_composition.py"),
    Path("intelligence/live_execution_dispatch.py"),
    Path("intelligence/paper_broker_adapter.py"),
    Path("intelligence/execution_identity.py"),
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


BEFORE = {
    path: sha256_file(path)
    for path in PRODUCTION_FILES
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


print("=== CANONICAL PAPER E2E EXECUTION CERTIFICATION ===")

print("PRODUCTION FILE SNAPSHOT:")
for path, digest in BEFORE.items():
    print(f"  {path}: {digest}")


# ---------------------------------------------------------------------------
# 1. Build the real PAPER dispatch composition.
# ---------------------------------------------------------------------------

runtime = build_execution_dispatch_runtime()

print("\nRUNTIME:")
print("  class:", type(runtime))
print("  module:", type(runtime).__module__)

require(
    type(runtime).__name__ == "ExecutionDispatchRuntime",
    "Unexpected dispatch runtime",
)

# Runtime must expose real PAPER adapter callables.
paper_authorizer = runtime.paper_authorizer
paper_executor = runtime.paper_executor
paper_rollback = runtime.paper_rollback

require(callable(paper_authorizer), "PAPER authorizer missing")
require(callable(paper_executor), "PAPER executor missing")
require(callable(paper_rollback), "PAPER rollback missing")

# The executor must belong to the real ExecutionAdapter.
paper_adapter = getattr(paper_executor, "__self__", None)

require(
    paper_adapter is not None,
    "PAPER executor is not a bound ExecutionAdapter method",
)

require(
    type(paper_adapter).__name__ == "ExecutionAdapter",
    "Unexpected PAPER executor owner",
)


# ---------------------------------------------------------------------------
# 2. Verify the real in-memory PaperBrokerAdapter is underneath.
# ---------------------------------------------------------------------------

paper_broker = getattr(paper_adapter, "broker", None)

require(
    paper_broker is not None,
    "ExecutionAdapter has no broker",
)

require(
    type(paper_broker).__name__ == "PaperBrokerAdapter",
    "PAPER runtime is not backed by PaperBrokerAdapter",
)

print("  adapter:", type(paper_adapter).__name__)
print("  broker :", type(paper_broker).__name__)


# ---------------------------------------------------------------------------
# 3. Build a canonical authorized execution contract.
#
# This represents the output already authorized by ExecutionGatewayV2.
# We deliberately provide the same fields main.py consumes downstream.
# ---------------------------------------------------------------------------

canonical_execution = {
    "ready": True,
    "approved": True,
    "status": "EXECUTE",
    "gate": "AUTHORIZED",
    "mode": "PAPER",
    "broker": "Paper",
    "symbol": "BTCUSDT",
    "decision": "ENTER_LONG",
    "entry": 100.0,
    "stop_loss": 95.0,
    "targets": [105.0, 110.0, 120.0],
    "position_size": 2.0,
    "risk_amount": 10.0,
    "risk_percent": 1.0,
    "structural_readiness": "CONFIRMED",
    "location_quality": "INTERACTING",
    "entry_distance_atr": 0.10,
    "authorization_id": (
        "BTCUSDT:ENTER_LONG:100.00000000:95.00000000:"
        "2.00000000:1.0000"
    ),
    "client_order_id": "JQX-E2E-PAPER-0001",
    "instrument_token": "E2E-BTCUSDT",
    "timeframe": "15m",
}


# Stable upstream snapshot.
upstream = dict(canonical_execution)


# ---------------------------------------------------------------------------
# 4. Canonical identity binding.
# ---------------------------------------------------------------------------

bound = bind_execution_identity(canonical_execution)

require(bound is not canonical_execution, "Identity binder did not copy execution")

for key in (
    "authorization_id",
    "client_order_id",
    "symbol",
    "decision",
    "entry",
    "stop_loss",
    "targets",
    "position_size",
    "risk_amount",
    "risk_percent",
    "mode",
):
    require(
        bound.get(key) == upstream.get(key),
        f"Identity binding changed {key}",
    )

trade_uuid = bound.get("trade_uuid")

require(
    isinstance(trade_uuid, str) and trade_uuid.strip(),
    "Identity binder failed to allocate trade_uuid",
)

print("\nIDENTITY BINDING: PASS")
print("  authorization_id:", bound["authorization_id"])
print("  client_order_id :", bound["client_order_id"])
print("  trade_uuid      :", trade_uuid)


# ---------------------------------------------------------------------------
# 5. Actual PAPER authorization.
# ---------------------------------------------------------------------------

authorization = paper_authorizer(bound)

require(isinstance(authorization, dict), "PAPER authorizer returned invalid object")
require(authorization.get("authorized") is True, "PAPER authorization failed")

execution = authorization.get("execution")

require(
    isinstance(execution, dict),
    "PAPER authorizer returned no execution",
)


# The adapter's authorization result must preserve canonical identity.
for key in (
    "authorization_id",
    "client_order_id",
    "trade_uuid",
    "symbol",
    "decision",
    "entry",
    "stop_loss",
    "targets",
    "position_size",
    "risk_amount",
    "risk_percent",
    "mode",
):
    require(
        execution.get(key) == bound.get(key),
        f"Authorization changed {key}",
    )

print("PAPER AUTHORIZATION: PASS")


# ---------------------------------------------------------------------------
# 6. Verify dispatch call object identity/content.
#
# Replace ONLY the runtime's callable attribute with a spy wrapper.
# No production module/source is modified.
# ---------------------------------------------------------------------------

original_paper_executor = runtime.paper_executor
dispatch_observation = {}
live_calls = []


def spy_paper_executor(execution_arg, fill_quantity=None):
    dispatch_observation["object_id"] = id(execution_arg)
    dispatch_observation["execution"] = dict(execution_arg)
    dispatch_observation["fill_quantity"] = fill_quantity
    return original_paper_executor(
        execution_arg,
        fill_quantity=fill_quantity,
    )


runtime.paper_executor = spy_paper_executor


original_live_runtime = runtime.live_runtime


def forbidden_live_submit(*args, **kwargs):
    live_calls.append(
        {
            "args": args,
            "kwargs": kwargs,
        }
    )
    raise AssertionError(
        "LIVE transport was invoked during PAPER certification"
    )


if hasattr(original_live_runtime, "submit_live"):
    original_live_runtime.submit_live = forbidden_live_submit


# ---------------------------------------------------------------------------
# 7. Actual dispatch through ExecutionDispatchRuntime.
# ---------------------------------------------------------------------------

result = runtime.dispatch(
    execution,
)

require(
    isinstance(result, dict),
    "PAPER dispatch returned invalid result",
)

require(
    dispatch_observation.get("object_id") == id(execution),
    "Dispatch did not receive the canonical authorized execution object",
)

observed = dispatch_observation["execution"]


# ---------------------------------------------------------------------------
# 8. Exact identity preservation across dispatch.
# ---------------------------------------------------------------------------

identity_fields = (
    "authorization_id",
    "client_order_id",
    "trade_uuid",
    "symbol",
    "decision",
    "entry",
    "stop_loss",
    "targets",
    "position_size",
    "risk_amount",
    "risk_percent",
    "mode",
)

for key in identity_fields:
    require(
        observed.get(key) == execution.get(key),
        f"Dispatch changed {key}",
    )


# ---------------------------------------------------------------------------
# 9. Result identity preservation.
# ---------------------------------------------------------------------------

require(
    result.get("authorization_id") == execution["authorization_id"],
    "Returned authorization_id mismatch",
)

result_order = result.get("order") or {}

require(
    result_order.get("authorization_id") == execution["authorization_id"],
    "Broker order authorization_id mismatch",
)

require(
    result_order.get("client_order_id") == execution["client_order_id"],
    "Broker order client_order_id mismatch",
)

require(
    result_order.get("symbol") == execution["symbol"],
    "Broker order symbol mismatch",
)

require(
    result_order.get("side") == "BUY",
    "Unexpected PAPER broker side",
)

require(
    float(result_order.get("requested_qty", 0.0))
    == execution["position_size"],
    "Broker requested quantity mismatch",
)

require(
    float(result_order.get("filled_qty", 0.0))
    == execution["position_size"],
    "Broker filled quantity mismatch",
)

require(
    float(result_order.get("remaining_qty", -1.0)) == 0.0,
    "Broker remaining quantity mismatch",
)

require(
    float(result_order.get("average_fill_price", 0.0))
    == execution["entry"],
    "Broker average fill price mismatch",
)

require(
    float(result.get("fill_price", 0.0)) == execution["entry"],
    "Execution result fill price mismatch",
)


# ---------------------------------------------------------------------------
# 10. Full PAPER lifecycle must have completed.
# ---------------------------------------------------------------------------

require(
    result.get("order_status") == "FILLED",
    f"Unexpected PAPER order status: {result.get('order_status')!r}",
)

require(
    result.get("authorized") is True,
    "PAPER result is not authorized",
)

require(
    result.get("mode") == "PAPER",
    f"Unexpected PAPER result mode: {result.get('mode')!r}",
)

require(
    float(result.get("requested_quantity", 0.0))
    == execution["position_size"],
    "PAPER requested quantity mismatch",
)

require(
    float(result.get("filled_quantity", 0.0))
    == execution["position_size"],
    "PAPER filled quantity mismatch",
)

require(
    float(result.get("remaining_quantity", -1.0)) == 0.0,
    "PAPER remaining quantity mismatch",
)

require(
    result.get("residual_cancelled") is True,
    "PAPER residual cancellation invariant failed",
)

require(
    result_order.get("status") == "FILLED",
    f"Unexpected broker order status: {result_order.get('status')!r}",
)

require(
    float(result.get("filled_quantity", 0.0)) == execution["position_size"],
    "Filled quantity mismatch",
)

protection = result.get("protection") or {}

require(
    protection,
    "PAPER execution returned no protection",
)

require(
    protection.get("authorization_id") == execution["authorization_id"],
    "Protection authorization_id mismatch",
)

require(
    float(protection.get("quantity", 0.0)) == execution["position_size"],
    "Protection quantity mismatch",
)

require(
    float(protection.get("stop_loss", 0.0)) == execution["stop_loss"],
    "Protection stop mismatch",
)

require(
    protection.get("targets") == execution["targets"],
    "Protection target mismatch",
)

reconciliation = result.get("position_reconciliation") or {}

require(
    reconciliation.get("reconciled") is True,
    "Position reconciliation failed",
)

protection_reconciliation = result.get("protection_reconciliation") or {}

require(
    protection_reconciliation.get("reconciled") is True,
    "Protection reconciliation failed",
)


# ---------------------------------------------------------------------------
# 11. Verify broker internal state.
# ---------------------------------------------------------------------------

authorization_id = execution["authorization_id"]

order = paper_broker.get_order(authorization_id)
position = paper_broker.get_position(authorization_id)

require(
    isinstance(order, dict),
    "Paper broker did not retain order",
)

require(
    isinstance(position, dict),
    "Paper broker did not retain position",
)

require(
    order.get("authorization_id") == authorization_id,
    "Stored order identity mismatch",
)

require(
    position.get("authorization_id") == authorization_id,
    "Stored position identity mismatch",
)

require(
    float(position.get("quantity", 0.0)) == execution["position_size"],
    "Stored position quantity mismatch",
)


# ---------------------------------------------------------------------------
# 12. LIVE must remain untouched.
# ---------------------------------------------------------------------------

require(
    len(live_calls) == 0,
    "LIVE submit_live was invoked",
)

require(
    type(original_live_runtime).__name__ == "_LiveUnavailableRuntime",
    "Unexpected LIVE runtime object in PAPER composition",
)


# Explicit PAPER activation must fail closed.
try:
    runtime.dispatch(
        execution,
        activation_requested=True,
    )
except Exception as exc:
    activation_error = str(exc)
else:
    raise AssertionError(
        "PAPER dispatch accepted activation_requested=True"
    )

require(
    "activation request is invalid for PAPER" in activation_error,
    "Unexpected PAPER activation guard message",
)

require(
    len(live_calls) == 0,
    "LIVE runtime was touched by PAPER activation test",
)


# ---------------------------------------------------------------------------
# 13. Production source immutability.
# ---------------------------------------------------------------------------

AFTER = {
    path: sha256_file(path)
    for path in PRODUCTION_FILES
}

for path in PRODUCTION_FILES:
    require(
        AFTER[path] == BEFORE[path],
        f"PRODUCTION FILE MODIFIED: {path}",
    )


# ---------------------------------------------------------------------------
# Final report.
# ---------------------------------------------------------------------------

print("\n=== CANONICAL PAPER E2E RESULTS ===")
print("IDENTITY BINDING                         PASS")
print("PAPER AUTHORIZATION                      PASS")
print("DISPATCH RECEIVED CANONICAL CONTRACT    PASS")
print("AUTHORIZATION ID PRESERVED               PASS")
print("CLIENT ORDER ID PRESERVED                PASS")
print("TRADE UUID PRESERVED                     PASS")
print("SYMBOL / DECISION PRESERVED              PASS")
print("ENTRY / STOP / TARGETS PRESERVED         PASS")
print("POSITION SIZE PRESERVED                  PASS")
print("PAPER ENTRY FILLED                       PASS")
print("PAPER PROTECTION CREATED                 PASS")
print("POSITION RECONCILIATION                  PASS")
print("PROTECTION RECONCILIATION                PASS")
print("PAPER BROKER STATE                       PASS")
print("LIVE SUBMISSION COUNT                    0")
print("PAPER ACTIVATION GUARD                   PASS")
print("PRODUCTION FILE IMMUTABILITY              PASS")

print("\n=== CERTIFICATION RESULT ===")
print("CANONICAL PAPER E2E EXECUTION: PASS")
print("NO PRODUCTION FILES MODIFIED")
