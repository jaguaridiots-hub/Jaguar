from intelligence.execution_adapter import ExecutionAdapter
import intelligence.paper_post_fill as pp


# ============================================================
# ADAPTER BOUNDARY
# ============================================================

class FakeBroker:
    CLOSED = "CLOSED"

    def __init__(self):
        self.protection_called = False
        self.reconcile_called = False
        self.rollback_called = False

    def submit_entry(self, contract, fill_quantity=None):
        return {
            "authorization_id": contract["authorization_id"],
            "client_order_id": contract["client_order_id"],
            "broker_order_id": "PAPER-POS31-ADAPTER",
            "requested_qty": 1.0,
            "filled_qty": 0.5,
            "remaining_qty": 0.0,
            "average_fill_price": 100.0,
            "status": "FILLED",
        }

    def close_position(self, authorization_id, price):
        self.rollback_called = True
        return {
            "status": self.CLOSED,
            "authorization_id": authorization_id,
            "rolled_back": True,
        }

    def submit_protection(self, execution, filled_quantity):
        self.protection_called = True
        raise AssertionError(
            "Protection must not execute after quantity rejection"
        )

    def reconcile(self, authorization_id, filled_quantity):
        self.reconcile_called = True
        raise AssertionError(
            "Position reconciliation must not execute after quantity rejection"
        )

    def reconcile_protection(self, execution, filled_quantity):
        raise AssertionError(
            "Protection reconciliation must not execute after quantity rejection"
        )


adapter = ExecutionAdapter.__new__(ExecutionAdapter)
adapter.broker = FakeBroker()
adapter.PAPER = "PAPER"
adapter.authorize = lambda execution: {
    "execution": dict(execution)
}

execution = {
    "mode": "PAPER",
    "authorization_id": "AUTH-R56-POS31-ADAPTER",
    "client_order_id": "CLIENT-R56-POS31-ADAPTER",
    "position_size": 1.0,
    "entry": 100.0,
}

adapter_rejected = False

try:
    adapter.execute(execution)
except RuntimeError as exc:
    adapter_rejected = True
    assert "quantity/status mismatch" in str(exc)

assert adapter_rejected
assert adapter.broker.rollback_called
assert not adapter.broker.protection_called
assert not adapter.broker.reconcile_called

print("ADAPTER_FALSE_FULL_FILL_REJECTED=PASS")


# ============================================================
# DURABLE RECONCILIATION BOUNDARY
# ============================================================

intent = {
    "authorization_id": "AUTH-R56-POS31-DURABLE",
    "trade_uuid": "TRADE-R56-POS31-DURABLE",
    "client_order_id": "CLIENT-R56-POS31-DURABLE",
    "symbol": "BTCUSDT",
    "timeframe": "15m",
    "mode": "PAPER",
    "decision": "LONG",
    "quantity": 1.0,
    "stop_loss": 95.0,
    "take_profit": 110.0,
    "status": "SUBMITTED",
}

execution = {
    "ready": True,
    "approved": True,
    "status": "EXECUTE",
    "gate": "AUTHORIZED",
    "mode": "PAPER",
    "decision": "ENTER_LONG",
    "entry": 100.0,
    "stop_loss": 95.0,
    "targets": [110.0, 115.0, 120.0],
    "position_size": 1.0,
    "risk_amount": 5.0,
    "authorization_id": intent["authorization_id"],
    "client_order_id": intent["client_order_id"],
    "symbol": "BTCUSDT",
    "timeframe": "15m",
}

execution_result = {
    "authorization_id": intent["authorization_id"],
    "requested_quantity": 1.0,
    "filled_quantity": 0.5,
    "remaining_quantity": 0.0,
    "fill_price": 100.0,
    "order_status": "FILLED",
    "order": {
        "authorization_id": intent["authorization_id"],
        "client_order_id": intent["client_order_id"],
        "broker_order_id": "PAPER-R56-POS31-DURABLE",
        "symbol": "BTCUSDT",
        "requested_qty": 1.0,
        "filled_qty": 0.5,
        "remaining_qty": 0.0,
        "average_fill_price": 100.0,
        "status": "FILLED",
    },
}

calls = []


def fake_get_execution_intent(auth):
    assert auth == intent["authorization_id"]
    return intent


def fake_update_execution_intent(auth, *, status=None, **kwargs):
    calls.append(("update_intent", auth, status))
    if status is not None:
        intent["status"] = status


original_get = pp.get_execution_intent
original_update = pp.update_execution_intent

pp.get_execution_intent = fake_get_execution_intent
pp.update_execution_intent = fake_update_execution_intent

durable_rejected = False

try:
    try:
        pp._persist_paper_durable_lifecycle(
            execution=dict(execution),
            execution_result=execution_result,
            authorization_id=intent["authorization_id"],
            filled_quantity=0.5,
            authorized_stop=95.0,
            authorized_targets=[110.0, 115.0, 120.0],
        )
    except RuntimeError as exc:
        durable_rejected = True
        assert "quantity authority mismatch" in str(exc)
finally:
    pp.get_execution_intent = original_get
    pp.update_execution_intent = original_update

assert durable_rejected
assert intent["status"] == "SUBMITTED"
assert not any(
    call[2] == "RECONCILED"
    for call in calls
    if call[0] == "update_intent"
)

print("DURABLE_FALSE_FULL_FILL_REJECTED=PASS")
print("R56_POS31_QUANTITY_AUTHORITY: PASS")
