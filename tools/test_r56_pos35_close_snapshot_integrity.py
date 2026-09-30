import hashlib
import json
from datetime import datetime as RealDateTime
from unittest.mock import patch

import research.recorder as recorder


class FakeDateTime(RealDateTime):
    calls = 0

    @classmethod
    def now(cls, tz=None):
        cls.calls += 1
        return cls(2026, 9, 30, 12, 0, 0, cls.calls)


def checksum(snapshot):
    return hashlib.sha256(
        json.dumps(snapshot, sort_keys=True).encode()
    ).hexdigest()


def run_case(exit_time=None):
    FakeDateTime.calls = 0
    captured = {}

    def fake_init_db():
        captured["init_db"] = True

    def fake_update_close_trade(uuid, close_data):
        captured["uuid"] = uuid
        captured["close_data"] = dict(close_data)

    with patch.object(recorder, "datetime", FakeDateTime), \
         patch.object(recorder, "init_db", fake_init_db), \
         patch.object(recorder, "update_close_trade", fake_update_close_trade):

        recorder.record_trade_close(
            "R56-POS35-PERMANENT",
            exit_price=110.0,
            pnl=8.5,
            r_multiple=1.7,
            win_loss=True,
            holding_time=12,
            exit_time=exit_time,
        )

    assert "close_data" in captured

    close_data = captured["close_data"]
    snapshot = json.loads(close_data["snapshot_close"])

    assert close_data["snapshot_close_checksum"] == checksum(snapshot)
    assert close_data["close_time"] == snapshot["timestamp"]

    if exit_time is None:
        assert FakeDateTime.calls == 1
    else:
        assert FakeDateTime.calls == 0
        assert snapshot["timestamp"] == exit_time

    return close_data, snapshot


# Case A: runtime-generated timestamp must be reused everywhere.
close_data, snapshot = run_case()

print("R56_POS35_GENERATED_TIMESTAMP_SINGLE_SOURCE: PASS")
print("R56_POS35_GENERATED_SNAPSHOT_CHECKSUM_MATCH: PASS")
print("R56_POS35_GENERATED_CLOSE_TIME_ALIGNMENT: PASS")

# Case B: explicit exit_time must become the canonical snapshot timestamp.
explicit_time = "2030-01-02T03:04:05"
close_data, snapshot = run_case(explicit_time)

print("R56_POS35_EXPLICIT_EXIT_TIME_CANONICAL: PASS")
print("R56_POS35_EXPLICIT_TIMESTAMP_CHECKSUM_MATCH: PASS")
print("R56_POS35_EXPLICIT_CLOSE_TIME_ALIGNMENT: PASS")

print("R56-POS-35-PERMANENT-WITNESS: PASS")
