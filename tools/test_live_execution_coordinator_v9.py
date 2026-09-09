import os
import tempfile
from importlib import reload

from intelligence.live_execution_coordinator import (
    LiveExecutionCoordinator,
)
from research import database as db


class FakeLiveBroker:
    EXECUTION_MODE = "LIVE"

    def __init__(self):
        self.submit_calls = 0
        self.raise_after_submit = False
        self.history = []

    def submit_entry(self, execution):
        self.submit_calls += 1

        broker_id = f"UP-{self.submit_calls:03d}"

        self.history.append({
            "order_id": broker_id,
            "tag": execution["client_order_id"],
            "instrument_token": execution["instrument_token"],
            "transaction_type": (
                "BUY"
                if execution["decision"] == "LONG"
                else "SELL"
            ),
            "quantity": execution["quantity"],
            "status": "OPEN",
        })

        if self.raise_after_submit:
            raise RuntimeError("lost broker response")

        return {
            "broker_order_id": broker_id,
            "status": "SUBMITTED",
        }

    def get_order_history(
        self,
        *,
        client_order_id=None,
        broker_order_id=None,
    ):
        if client_order_id is not None:
            return [
                dict(row)
                for row in self.history
                if row["tag"] == client_order_id
            ]

        if broker_order_id is not None:
            return [
                dict(row)
                for row in self.history
                if row["order_id"] == broker_order_id
            ]

        raise AssertionError("identity required")


def fresh_db():
    tmp = tempfile.TemporaryDirectory()
    os.environ["JAGUAR_DB_PATH"] = os.path.join(
        tmp.name,
        "coordinator.sqlite",
    )
    reload(db)
    conn = db.init_db()
    conn.close()
    return tmp


def execution(
    authorization_id,
    client_order_id,
    decision="LONG",
):
    return {
        "authorization_id": authorization_id,
        "trade_uuid": authorization_id + "-TRADE",
        "client_order_id": client_order_id,
        "symbol": "NSE_EQ|TEST",
        "timeframe": "15m",
        "instrument_token": "NSE_EQ|TEST",
        "mode": "LIVE",
        "decision": decision,
        "quantity": 10,
        "requested_price": 100.0,
        "stop_loss": 95.0,
        "take_profit": 110.0,
        "ready": True,
        "approved": True,
        "status": "EXECUTE",
        "gate": "AUTHORIZED",
    }


# Happy path + idempotence
tmp = fresh_db()
broker = FakeLiveBroker()
c = LiveExecutionCoordinator(broker, database_module=db)

r = c.start_submission(
    execution("AUTH-D21-001", "JGX-D21-001")
)

assert r["status"] == "SUBMITTED"
assert r["broker_order_id"] == "UP-001"
assert broker.submit_calls == 1

row = db.get_execution_submission_by_client_order_id("JGX-D21-001")
assert row["status"] == "LINEAGE_PERSISTED"
assert row["broker_order_id"] == "UP-001"

orders = db.list_execution_orders("AUTH-D21-001")
assert len(orders) == 1

parent = db.get_execution_intent("AUTH-D21-001")
assert parent["status"] == "SUBMITTED"

r2 = c.start_submission(
    execution("AUTH-D21-001", "JGX-D21-001")
)

assert r2["broker_order_id"] == "UP-001"
assert broker.submit_calls == 1

print("D21_HAPPY_PATH: PASS")
print("D21_DUPLICATE_SUBMISSION_PREVENTED: PASS")


# Lost response: recover by tag, no resubmission
tmp = fresh_db()
broker = FakeLiveBroker()
broker.raise_after_submit = True
c = LiveExecutionCoordinator(broker, database_module=db)

r = c.start_submission(
    execution("AUTH-D21-002", "JGX-D21-002")
)

assert r["status"] == "SUBMITTING"
assert r["action"] == "RECOVERY_REQUIRED"
assert broker.submit_calls == 1

r = c.recover_submission("AUTH-D21-002")

assert r["status"] == "SUBMITTED"
assert r["broker_order_id"] == "UP-001"
assert broker.submit_calls == 1

row = db.get_execution_submission_by_client_order_id("JGX-D21-002")
assert row["status"] == "LINEAGE_PERSISTED"

orders = db.list_execution_orders("AUTH-D21-002")
assert len(orders) == 1

r = c.start_submission(
    execution("AUTH-D21-002", "JGX-D21-002")
)

assert r["status"] == "SUBMITTED"
assert broker.submit_calls == 1

print("D21_LOST_RESPONSE_RECOVERY: PASS")
print("D21_NO_AUTOMATIC_RESUBMISSION: PASS")


# Zero history during lost-response recovery -> HALTED
tmp = fresh_db()
broker = FakeLiveBroker()
broker.raise_after_submit = True
c = LiveExecutionCoordinator(broker, database_module=db)

r = c.start_submission(
    execution("AUTH-D21-003", "JGX-D21-003")
)

assert r["status"] == "SUBMITTING"
assert r["action"] == "RECOVERY_REQUIRED"
assert broker.submit_calls == 1

broker.history = []

r = c.recover_submission("AUTH-D21-003")

assert r["status"] == "HALTED"
assert db.get_execution_intent("AUTH-D21-003")["status"] == "HALTED"
assert db.get_execution_submission_by_client_order_id(
    "JGX-D21-003"
)["status"] == "HALTED"

print("D21_ZERO_HISTORY_FAIL_CLOSED: PASS")


# Multiple history records during lost-response recovery -> HALTED
tmp = fresh_db()
broker = FakeLiveBroker()
broker.raise_after_submit = True
c = LiveExecutionCoordinator(broker, database_module=db)

r = c.start_submission(
    execution("AUTH-D21-004", "JGX-D21-004")
)

assert r["status"] == "SUBMITTING"
assert r["action"] == "RECOVERY_REQUIRED"
assert broker.submit_calls == 1

broker.raise_after_submit = False
broker.history.append(dict(broker.history[0]))
broker.history[1]["order_id"] = "UP-002"

r = c.recover_submission("AUTH-D21-004")

assert r["status"] == "HALTED"

print("D21_MULTIPLE_HISTORY_FAIL_CLOSED: PASS")


# Direction mismatch during lost-response recovery -> HALTED
tmp = fresh_db()
broker = FakeLiveBroker()
broker.raise_after_submit = True
c = LiveExecutionCoordinator(broker, database_module=db)

r = c.start_submission(
    execution("AUTH-D21-005", "JGX-D21-005")
)

assert r["status"] == "SUBMITTING"
assert r["action"] == "RECOVERY_REQUIRED"
assert broker.submit_calls == 1

broker.raise_after_submit = False
broker.history[0]["transaction_type"] = "SELL"

r = c.recover_submission("AUTH-D21-005")

assert r["status"] == "HALTED"

print("D21_DIRECTION_MISMATCH_FAIL_CLOSED: PASS")


# Instrument mismatch during lost-response recovery -> HALTED
tmp = fresh_db()
broker = FakeLiveBroker()
broker.raise_after_submit = True
c = LiveExecutionCoordinator(broker, database_module=db)

r = c.start_submission(
    execution("AUTH-D21-006", "JGX-D21-006")
)

assert r["status"] == "SUBMITTING"
assert r["action"] == "RECOVERY_REQUIRED"
assert broker.submit_calls == 1

broker.raise_after_submit = False
broker.history[0]["instrument_token"] = "NSE_EQ|WRONG"

r = c.recover_submission("AUTH-D21-006")

assert r["status"] == "HALTED"

print("D21_INSTRUMENT_MISMATCH_FAIL_CLOSED: PASS")


# Paper broker rejected
class PaperBroker:
    EXECUTION_MODE = "PAPER"

    def submit_entry(self, execution):
        raise AssertionError("must not execute")

    def get_order_history(self, **kwargs):
        raise AssertionError("must not observe")


try:
    LiveExecutionCoordinator(PaperBroker(), database_module=db)
except RuntimeError:
    pass
else:
    raise AssertionError("Paper broker accepted")


print("D21_PAPER_BROKER_FAIL_CLOSED: PASS")


# Unauthorized execution rejected before broker call
tmp = fresh_db()
broker = FakeLiveBroker()
c = LiveExecutionCoordinator(broker, database_module=db)

bad = execution("AUTH-D21-007", "JGX-D21-007")
bad["approved"] = False

try:
    c.start_submission(bad)
except RuntimeError:
    pass
else:
    raise AssertionError("Unauthorized execution accepted")

assert broker.submit_calls == 0

print("D21_UNAUTHORIZED_EXECUTION_FAIL_CLOSED: PASS")
print("D21_COORDINATOR_CONTRACT: PASS")
