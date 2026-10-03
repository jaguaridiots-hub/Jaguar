#!/usr/bin/env python3

import os
import tempfile
from datetime import datetime, timezone


AUTH = "AUTH-PAPER-RECOVERY-0001"
TRADE_UUID = "TRADE-PAPER-RECOVERY-0001"
CLIENT_ORDER_ID = "JQX-PAPER-RECOVERY-0001"
SYMBOL = "BTCUSDT"
TIMEFRAME = "15m"
MODE = "PAPER"
DECISION = "LONG"
QUANTITY = 2.0
ENTRY = 100.0
STOP = 95.0
TARGET = 110.0
RUN_ID = "RUN-PAPER-RECOVERY-0001"


def now():
    return datetime.now(timezone.utc).isoformat()


def intent():
    ts = now()
    return {
        "authorization_id": AUTH,
        "trade_uuid": TRADE_UUID,
        "client_order_id": CLIENT_ORDER_ID,
        "symbol": SYMBOL,
        "timeframe": TIMEFRAME,
        "mode": MODE,
        "decision": DECISION,
        "quantity": QUANTITY,
        "requested_price": ENTRY,
        "stop_loss": STOP,
        "take_profit": TARGET,
        "run_id": RUN_ID,
        "status": "AUTHORIZED",
        "created_at": ts,
        "updated_at": ts,
    }


def open_trade():
    ts = now()
    return {
        "uuid": TRADE_UUID,
        "open_time": ts,
        "symbol": SYMBOL,
        "timeframe": TIMEFRAME,
        "mode": MODE,
        "entry_price": ENTRY,
        "stop_loss": STOP,
        "take_profit": TARGET,
        "decision": "ENTER_LONG",
        "run_id": RUN_ID,
        "success": 1,
        "asset_class": "CRYPTO",
        "authorization_id": AUTH,
        "status": "OPEN",
    }


def execution_contract():
    return {
        "authorization_id": AUTH,
        "trade_uuid": TRADE_UUID,
        "client_order_id": CLIENT_ORDER_ID,
        "symbol": SYMBOL,
        "timeframe": TIMEFRAME,
        "mode": MODE,
        "decision": "ENTER_LONG",
        "position_size": QUANTITY,
        "entry": ENTRY,
        "stop_loss": STOP,
        "targets": [TARGET],
    }


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def identity_tuple(row):
    return (
        row["authorization_id"],
        row["trade_uuid"],
        row["client_order_id"],
        row["symbol"],
        row["timeframe"],
        row["mode"],
        row["decision"],
        float(row["quantity"]),
        float(row["requested_price"]),
        float(row["stop_loss"]),
        float(row["take_profit"]),
    )


def main():
    fd, path = tempfile.mkstemp(
        prefix="jaguar-paper-recovery-",
        suffix=".db",
    )
    os.close(fd)

    os.environ["JAGUAR_DB_PATH"] = path

    import importlib
    import research.database as db
    import intelligence.execution_recovery as recovery
    from intelligence.paper_broker_adapter import PaperBrokerAdapter

    db = importlib.reload(db)
    recovery = importlib.reload(recovery)

    try:
        db.init_db()

        print("=== DURABLE EXECUTION-INTENT RECOVERY CERTIFICATION ===")
        print("ISOLATED DB:", path)
        print("MODE:", MODE)
        print("EXTERNAL BROKER CALLS: 0")

        # ------------------------------------------------------------
        # 1. Durable AUTHORIZED intent.
        # ------------------------------------------------------------
        original_intent = intent()
        db.insert_execution_intent(original_intent)

        durable = dict(db.get_execution_intent(AUTH))
        assert_true(durable is not None, "AUTHORIZED intent was not persisted")
        assert_true(
            durable["status"] == "AUTHORIZED",
            f"Unexpected initial status: {durable['status']}",
        )

        baseline_identity = identity_tuple(durable)

        print("AUTHORIZED INTENT PERSISTENCE       PASS")

        # ------------------------------------------------------------
        # 2. Real Paper broker submission.
        # ------------------------------------------------------------
        class CountingPaperBroker(PaperBrokerAdapter):
            def __init__(self):
                super().__init__()
                self.submit_calls = 0

            def submit_entry(self, execution, fill_quantity=None):
                self.submit_calls += 1
                return super().submit_entry(
                    execution,
                    fill_quantity=fill_quantity,
                )

        broker = CountingPaperBroker()
        execution = execution_contract()

        broker_result = broker.submit_entry(execution)

        assert_true(
            broker_result.get("status") == "FILLED",
            f"Paper submission did not fill: {broker_result}",
        )
        assert_true(
            broker.submit_calls == 1,
            f"Unexpected submit call count: {broker.submit_calls}",
        )

        assert_true(
            len(broker.orders) == 1,
            f"Expected one Paper order, found {len(broker.orders)}",
        )

        broker_order = dict(broker.orders[AUTH])
        broker_position = dict(broker.positions[AUTH])

        assert_true(
            broker_order["authorization_id"] == AUTH,
            "Broker authorization_id mismatch",
        )
        assert_true(
            broker_order["client_order_id"] == CLIENT_ORDER_ID,
            "Broker client_order_id mismatch",
        )
        assert_true(
            broker_order["symbol"] == SYMBOL,
            "Broker symbol mismatch",
        )
        assert_true(
            float(broker_order["requested_qty"]) == QUANTITY,
            "Broker requested quantity mismatch",
        )

        paper_broker_id = broker_order["broker_order_id"]

        print("PAPER BROKER SINGLE SUBMISSION      PASS")
        print("BROKER ORDER ID:", paper_broker_id)

        # ------------------------------------------------------------
        # 3. Simulate main.py boundary:
        #    broker succeeds, SUBMITTED persistence fails.
        #
        #    We intentionally DO NOT update the intent. This leaves
        #    the durable journal at AUTHORIZED exactly as a process
        #    failure between broker success and local persistence
        #    would leave it.
        # ------------------------------------------------------------
        original_status = durable["status"]

        assert_true(
            original_status == "AUTHORIZED",
            "Pre-failure durable status was not AUTHORIZED",
        )

        print("SIMULATED SUBMITTED PERSISTENCE FAIL PASS")

        after_failure = dict(db.get_execution_intent(AUTH))
        assert_true(
            after_failure["status"] == "AUTHORIZED",
            "Failure simulation did not preserve AUTHORIZED state",
        )

        assert_true(
            len(broker.orders) == 1,
            "Broker order disappeared after simulated persistence failure",
        )

        # ------------------------------------------------------------
        # 4. First recovery pass.
        #    Existing broker evidence is observed.
        #    No broker mutation is permitted.
        # ------------------------------------------------------------
        def observer(intent_row):
            assert_true(
                intent_row["authorization_id"] == AUTH,
                "Recovery observer received wrong authorization_id",
            )
            return {
                "order": dict(broker.orders[AUTH]),
                "position": dict(broker.positions[AUTH]),
            }

        before_recovery_submit_calls = broker.submit_calls

        recovery_results_1 = recovery.reconcile_all(
            broker_observer=observer,
        )

        assert_true(
            len(recovery_results_1) == 1,
            f"Expected one recovery result, got {recovery_results_1}",
        )

        result_1 = recovery_results_1[0]

        assert_true(
            result_1["previous_status"] == "AUTHORIZED",
            f"Unexpected recovery previous state: {result_1}",
        )
        assert_true(
            result_1["status"] == "SUBMITTED",
            f"AUTHORIZED recovery did not reach SUBMITTED: {result_1}",
        )
        assert_true(
            result_1["broker_order_id"] == paper_broker_id,
            "Recovery assigned a different broker order ID",
        )

        assert_true(
            broker.submit_calls == before_recovery_submit_calls,
            "Recovery submitted a new broker order",
        )

        assert_true(
            len(broker.orders) == 1,
            "Recovery created a duplicate broker order",
        )

        recovered_submitted = dict(db.get_execution_intent(AUTH))

        assert_true(
            recovered_submitted["status"] == "SUBMITTED",
            f"Durable status not SUBMITTED: {recovered_submitted['status']}",
        )
        assert_true(
            identity_tuple(recovered_submitted) == baseline_identity,
            "Durable identity changed during AUTHORIZED -> SUBMITTED recovery",
        )
        assert_true(
            recovered_submitted["broker_order_id"] == paper_broker_id,
            "Durable broker_order_id mismatch after recovery",
        )

        print("AUTHORIZED -> SUBMITTED RECOVERY    PASS")
        print("IDENTITY PRESERVED                   PASS")
        print("NO DUPLICATE ORDER                   PASS")

        # ------------------------------------------------------------
        # 5. Create the durable OPEN trade that the V9 recovery
        #    contract requires before SUBMITTED -> RECONCILED.
        # ------------------------------------------------------------
        db.insert_open_trade(open_trade())

        recovered_trade = db.get_connection().execute(
            "SELECT * FROM trades WHERE uuid = ?",
            (TRADE_UUID,),
        ).fetchone()

        assert_true(
            recovered_trade is not None,
            "Durable OPEN trade was not created",
        )

        recovered_trade = dict(recovered_trade)

        assert_true(
            recovered_trade["status"] == "OPEN",
            "Durable trade is not OPEN",
        )
        assert_true(
            recovered_trade["uuid"] == TRADE_UUID,
            "Durable trade UUID mismatch",
        )
        assert_true(
            recovered_trade["authorization_id"] == AUTH,
            "Durable trade authorization_id mismatch",
        )

        print("DURABLE OPEN TRADE ESTABLISHED      PASS")

        # ------------------------------------------------------------
        # 6. Second recovery pass.
        #
        # The canonical durable lifecycle forbids:
        #     SUBMITTED -> RECONCILED
        #
        # Generic recovery must fail closed rather than bypass:
        #     FILLED
        #       -> POSITION_RECONCILING
        #       -> PROTECTION_PENDING
        #       -> RECONCILED
        # ------------------------------------------------------------
        before_second_submit_calls = broker.submit_calls
        recovery_failed_closed = False

        try:
            recovery.reconcile_all(
                broker_observer=observer,
            )
        except RuntimeError as exc:
            recovery_failed_closed = (
                "SUBMITTED -> RECONCILED" in str(exc)
                and "invalid execution-intent transition" in str(exc)
            )
            print("LEGACY SHORTCUT REJECTED             PASS")
            print("ERROR:", exc)

        assert_true(
            recovery_failed_closed,
            "Generic recovery did not reject forbidden SUBMITTED -> RECONCILED shortcut",
        )

        current_after_failure = dict(db.get_execution_intent(AUTH))

        assert_true(
            current_after_failure["status"] == "SUBMITTED",
            "Forbidden shortcut changed durable status",
        )

        assert_true(
            current_after_failure["status"] != "RECONCILED",
            "Forbidden shortcut reached RECONCILED",
        )

        assert_true(
            identity_tuple(current_after_failure) == baseline_identity,
            "Durable identity changed during rejected shortcut",
        )

        assert_true(
            current_after_failure["broker_order_id"] == paper_broker_id,
            "Broker order identity changed during rejected shortcut",
        )

        assert_true(
            broker.submit_calls == before_second_submit_calls,
            "Recovery attempted a new broker submission",
        )

        assert_true(
            len(broker.orders) == 1,
            "Recovery created a duplicate broker order",
        )

        print("SUBMITTED STATE PRESERVED             PASS")
        print("IDENTITY PRESERVED AFTER REJECTION    PASS")
        print("NO DUPLICATE ORDER                    PASS")

        # ------------------------------------------------------------
        # 7. Repeat recovery after rejected shortcut.
        # canonical lifecycle forbids SUBMITTED -> RECONCILED
        # ------------------------------------------------------------
        before_repeat_submit_calls = broker.submit_calls

        repeat_failed_closed = False
        try:
            recovery.reconcile_all(
                broker_observer=observer,
            )
        except RuntimeError as exc:
            repeat_failed_closed = (
                "SUBMITTED -> RECONCILED" in str(exc)
                and "invalid execution-intent transition" in str(exc)
            )
            print("REPEAT SHORTCUT REJECTED              PASS")
            print("ERROR:", exc)

        assert_true(
            repeat_failed_closed,
            "repeat recovery must reject SUBMITTED -> RECONCILED",
        )

        repeated = dict(db.get_execution_intent(AUTH))

        assert_true(
            repeated["status"] == "SUBMITTED",
            "repeat recovery must preserve SUBMITTED state",
        )
        print("REPEAT STATUS PRESERVED               PASS")

        assert_true(
            identity_tuple(repeated) == baseline_identity,
            "repeat recovery must preserve execution identity",
        )
        print("REPEAT IDENTITY PRESERVED             PASS")

        assert_true(
            repeated["broker_order_id"] == paper_broker_id,
            "repeat recovery must preserve broker order identity",
        )

        assert_true(
            broker.submit_calls == before_repeat_submit_calls,
            "repeat recovery must not submit another broker order",
        )
        assert_true(
            len(broker.orders) == 1,
            "repeat recovery must not create another broker order",
        )
        print("REPEAT NO DUPLICATE ORDER             PASS")

        # ------------------------------------------------------------
        # 8. Final invariants.
        # ------------------------------------------------------------
        assert_true(
            broker.submit_calls == 1,
            f"Expected exactly one submit_entry call, got {broker.submit_calls}",
        )

        assert_true(
            list(broker.orders.keys()) == [AUTH],
            f"Unexpected Paper broker order identities: {broker.orders.keys()}",
        )

        assert_true(
            broker.orders[AUTH]["broker_order_id"] == paper_broker_id,
            "Paper broker order identity mutated",
        )

        print("BROKER-SIDE IDENTITY IMMUTABILITY     PASS")
        print("EXECUTION SUBMISSION COUNT == 1      PASS")

        print("\n=== CERTIFICATION RESULT ===")
        print("EXECUTION INTENT RECOVERY: PASS")
        print("BROKER-SUCCESS / PERSISTENCE-FAILURE: PASS")
        print("NO DUPLICATE PAPER ORDER: PASS")
        print("IDENTITY PRESERVATION: PASS")
        print("NO PRODUCTION FILES MODIFIED")
        print("ISOLATED DB ONLY")

    finally:
        try:
            os.unlink(path)
        except FileNotFoundError:
            pass


if __name__ == "__main__":
    main()
