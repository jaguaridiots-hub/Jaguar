"""R56-POS-22 runtime entry lifecycle atomicity gate."""

from pathlib import Path
import json
import tempfile

import intelligence.paper_post_fill as pp
import engine.state_manager as sm


def _make_state():
    class State:
        pass

    state = State()
    state.execution = {}
    state.symbol = "BTCUSDT"
    state.interval = "15m"
    state.mode = "SWING"
    state.price = 100.0
    state.high = 101.0
    state.low = 99.0
    state.volume = 10.0
    state._trade_id = None
    return state


def _make_position(events):
    class Position:
        def __init__(self):
            self.position = "NONE"
            self.entry = 0.0
            self.stop_loss = 0.0
            self.take_profit = 0.0
            self.pnl = 0.0
            self.position_size = 0.0
            self.initial_risk = 0.0
            self.trade_uuid = None

        def open_trade(
            self,
            side,
            entry,
            stop_loss,
            take_profit,
            position_size,
            initial_risk,
        ):
            events.append("position.open_trade")
            self.position = side
            self.entry = float(entry)
            self.stop_loss = float(stop_loss)
            self.take_profit = float(take_profit)
            self.position_size = float(position_size)
            self.initial_risk = float(initial_risk)
            self.trade_uuid = None

        def set_trade_uuid(self, trade_uuid):
            events.append("position.set_trade_uuid")
            if not isinstance(trade_uuid, str) or not trade_uuid.strip():
                raise RuntimeError("invalid test trade UUID")
            self.trade_uuid = trade_uuid

        def close_trade(self):
            events.append("position.close_trade")
            self.position = "NONE"
            self.entry = 0.0
            self.stop_loss = 0.0
            self.take_profit = 0.0
            self.pnl = 0.0
            self.position_size = 0.0
            self.initial_risk = 0.0
            self.trade_uuid = None

    return Position()


def _make_manager(events):
    class Manager:
        def __init__(self):
            self.activated = False

        def activate(self):
            events.append("manager.activate")
            self.activated = True

        def snapshot(self):
            return {
                "position_open": True,
                "trade_closed": False,
                "break_even": False,
                "trailing": False,
                "tp1_hit": False,
                "tp2_hit": False,
            }

    return Manager()


class Journal:
    def __init__(self, events):
        self.events = events

    def save(self, state, plan):
        self.events.append("journal.save")


def _execution_result():
    return {
        "filled_quantity": 1.0,
        "fill_price": 100.0,
        "order_status": "FILLED",
        "remaining_quantity": 0.0,
    }


def _patch_common(events, lifecycle_error=None):
    original_record = pp.record_trade_open
    original_lifecycle = pp._persist_paper_durable_lifecycle

    def fake_record_trade_open(*args, **kwargs):
        events.append("record_trade_open")
        return kwargs["trade_uuid"]

    def fake_lifecycle(*args, **kwargs):
        events.append("_persist_paper_durable_lifecycle")
        if lifecycle_error is not None:
            raise lifecycle_error

    pp.record_trade_open = fake_record_trade_open
    pp._persist_paper_durable_lifecycle = fake_lifecycle

    return original_record, original_lifecycle


def _restore_common(original_record, original_lifecycle):
    pp.record_trade_open = original_record
    pp._persist_paper_durable_lifecycle = original_lifecycle


def _run_success(direction):
    events = []
    state = _make_state()
    position = _make_position(events)
    manager = _make_manager(events)
    journal = Journal(events)

    trade_uuid = f"R56-POS22-{direction}"

    with tempfile.TemporaryDirectory(dir=".jaguar_audit") as td:
        state_file = Path(td) / "state.json"

        original_file = sm.FILE
        original_save = pp.save
        sm.FILE = str(state_file)

        save_calls = []

        def tracked_save(*args, **kwargs):
            manager_arg = args[2] if len(args) > 2 else kwargs.get("manager")
            save_calls.append(manager_arg)
            events.append("save(position,SYMBOL,manager)")
            return sm.save(*args, **kwargs)

        pp.save = tracked_save

        original_record, original_lifecycle = _patch_common(events)

        try:
            pp.execute_paper_post_fill(
                execution={},
                execution_result=_execution_result(),
                authorization_id=f"AUTH-{direction}",
                trade_uuid=trade_uuid,
                authorized_stop=(
                    90.0 if direction == "BUY" else 110.0
                ),
                authorized_targets=(
                    [110.0, 120.0]
                    if direction == "BUY"
                    else [90.0, 80.0]
                ),
                direction=direction,
                state=state,
                position=position,
                manager=manager,
                journal=journal,
                plan={},
                rollback_execution_if_pre_submission=lambda result: None,
                preserve_trade_for_recovery=lambda uuid: None,
                SYMBOL="BTCUSDT",
                TIMEFRAME="15m",
            )
        finally:
            _restore_common(original_record, original_lifecycle)
            pp.save = original_save
            sm.FILE = original_file

        expected = [
            "position.open_trade",
            "record_trade_open",
            "position.set_trade_uuid",
            "journal.save",
            "_persist_paper_durable_lifecycle",
            "manager.activate",
            "save(position,SYMBOL,manager)",
        ]

        assert events == expected, (
            f"{direction}: unexpected event order: {events}"
        )

        assert len(save_calls) == 1
        assert save_calls[0] is manager
        assert state_file.exists()

        persisted = json.loads(state_file.read_text())

        assert persisted["position"] == (
            "LONG" if direction == "BUY" else "SHORT"
        )
        assert persisted["trade_uuid"] == trade_uuid
        assert persisted["manager_state"]["position_open"] is True
        assert persisted["manager_state"]["trade_closed"] is False

        print(f"R56_POS22_RUNTIME_{direction}_ORDER: PASS")
        print(f"R56_POS22_RUNTIME_{direction}_MANAGER_STATE: PASS")


def _run_lifecycle_failure():
    events = []
    state = _make_state()
    position = _make_position(events)
    manager = _make_manager(events)
    journal = Journal(events)

    with tempfile.TemporaryDirectory(dir=".jaguar_audit") as td:
        state_file = Path(td) / "state.json"

        original_file = sm.FILE
        original_save = pp.save

        sm.FILE = str(state_file)

        save_calls = []

        def tracked_save(*args, **kwargs):
            manager_arg = args[2] if len(args) > 2 else kwargs.get("manager")
            save_calls.append(manager_arg)
            events.append("save(position,SYMBOL,manager)")
            return sm.save(*args, **kwargs)

        pp.save = tracked_save

        original_record, original_lifecycle = _patch_common(
            events,
            RuntimeError("INJECTED: durable lifecycle failure"),
        )

        try:
            try:
                pp.execute_paper_post_fill(
                    execution={},
                    execution_result=_execution_result(),
                    authorization_id="AUTH-FAIL",
                    trade_uuid="R56-POS22-FAIL",
                    authorized_stop=90.0,
                    authorized_targets=[110.0, 120.0],
                    direction="BUY",
                    state=state,
                    position=position,
                    manager=manager,
                    journal=journal,
                    plan={},
                    rollback_execution_if_pre_submission=lambda result: None,
                    preserve_trade_for_recovery=lambda uuid: None,
                    SYMBOL="BTCUSDT",
                    TIMEFRAME="15m",
                )
            except RuntimeError as exc:
                assert "Execution reconciliation persistence failed" in str(exc)
            else:
                raise AssertionError(
                    "Expected injected lifecycle failure"
                )
        finally:
            _restore_common(original_record, original_lifecycle)
            pp.save = original_save
            sm.FILE = original_file

        assert events == [
            "position.open_trade",
            "record_trade_open",
            "position.set_trade_uuid",
            "journal.save",
            "_persist_paper_durable_lifecycle",
        ], events

        assert save_calls == []
        assert not state_file.exists()
        assert manager.activated is False

        print("R56_POS22_RUNTIME_FAILURE_NO_EARLY_SAVE: PASS")
        print("R56_POS22_RUNTIME_FAILURE_NO_MANAGER_ACTIVATION: PASS")


def main():
    Path(".jaguar_audit").mkdir(exist_ok=True)

    _run_success("BUY")
    _run_success("SELL")
    _run_lifecycle_failure()

    print("R56_POS22_RUNTIME_ENTRY_ATOMICITY: PASS")


if __name__ == "__main__":
    main()
