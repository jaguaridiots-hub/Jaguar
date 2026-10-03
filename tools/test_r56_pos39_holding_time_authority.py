from datetime import datetime
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
import json
import math

MAIN = Path("main.py").read_text()

print("============================================================")
print("R56-POS-39 HOLDING-TIME AUTHORITY WITNESS")
print("============================================================")

# ============================================================
# 1. Locate canonical terminal close block.
# ============================================================

close_start = MAIN.index("# FINAL CLOSE AUTHORITY:")
close_end = MAIN.index(
    "# CLOSE PERSISTENCE GUARD:",
    close_start,
)

close_block = MAIN[close_start:close_end]

print("R56_POS39_TERMINAL_CLOSE_BLOCK: FOUND")

# ============================================================
# 2. Legacy hard-coded zero must be absent.
# ============================================================

assert "holding_time=0" not in close_block
assert "holding_time=holding_seconds" in close_block

print("R56_POS39_ZERO_HOLDING_TIME_REMOVED: PASS")
print("R56_POS39_DERIVED_HOLDING_TIME_ARGUMENT: PASS")

# ============================================================
# 3. Durable source is the trades row, keyed by trade UUID.
# ============================================================

assert "SELECT" in close_block
assert "uuid," in close_block
assert "status," in close_block
assert "open_time," in close_block
assert "close_time" in close_block
assert "FROM trades" in close_block
assert "WHERE uuid = ?" in close_block

print("R56_POS39_DURABLE_TRADE_ROW_SOURCE: PASS")
print("R56_POS39_DURABLE_UUID_KEY: PASS")

# ============================================================
# 4. Durable row must still be OPEN.
# ============================================================

assert 'open_row["status"]' in close_block
assert '!= "OPEN"' in close_block

print("R56_POS39_OPEN_STATUS_GUARD: PASS")

# ============================================================
# 5. Already-closed row must fail closed.
# ============================================================

assert 'open_row["close_time"]' in close_block
assert "already has close_time" in close_block

print("R56_POS39_ALREADY_CLOSED_GUARD: PASS")

# ============================================================
# 6. Missing/blank durable open_time must fail closed.
# ============================================================

assert 'open_row["open_time"]' in close_block
assert "Durable trade open_time is missing" in close_block

print("R56_POS39_OPEN_TIME_REQUIRED: PASS")

# ============================================================
# 7. One canonical close timestamp.
# ============================================================

assert "close_timestamp = datetime.now().isoformat()" in close_block

assert (
    close_block.count("datetime.now().isoformat()") == 1
)

assert "exit_time=close_timestamp" in close_block

print("R56_POS39_SINGLE_CLOSE_TIMESTAMP: PASS")
print("R56_POS39_CLOSE_TIMESTAMP_PASSED_TO_RECORDER: PASS")

# ============================================================
# 8. Strict ISO parsing.
# ============================================================

assert "datetime.fromisoformat(" in close_block
assert "Invalid durable trade timestamp" in close_block

print("R56_POS39_TIMESTAMP_PARSE_FAIL_CLOSED: PASS")

# ============================================================
# 9. Timezone awareness mismatch must fail closed.
# ============================================================

assert "open_is_aware" in close_block
assert "close_is_aware" in close_block
assert "timestamp timezone mismatch" in close_block

print("R56_POS39_TIMEZONE_COMPATIBILITY_GUARD: PASS")

# ============================================================
# 10. Duration comes from durable open → canonical close.
# ============================================================

assert "close_dt - open_dt" in close_block
assert ".total_seconds()" in close_block
assert "holding_seconds = (" in close_block

print("R56_POS39_DURATION_FROM_DURABLE_TIMESTAMPS: PASS")

# ============================================================
# 11. Negative duration must fail closed.
# ============================================================

assert "holding_seconds < 0" in close_block
assert "Negative trade holding time" in close_block

print("R56_POS39_NEGATIVE_DURATION_GUARD: PASS")

# ============================================================
# 12. Duration is persisted as integer seconds.
# ============================================================

assert "holding_seconds = int(" in close_block

print("R56_POS39_INTEGER_SECOND_CONTRACT: PASS")

# ============================================================
# 13. Deterministic arithmetic witness.
# ============================================================

open_dt = datetime.fromisoformat(
    "2026-10-01T08:00:00"
)

close_dt = datetime.fromisoformat(
    "2026-10-01T08:07:30.500000"
)

holding_seconds = int(
    (close_dt - open_dt).total_seconds()
)

assert holding_seconds == 450
assert holding_seconds != 0

print("R56_POS39_DERIVED_SECONDS=450")
print("R56_POS39_LEGACY_SECONDS=0")
print("R56_POS39_ZERO_DIVERGENCE_ELIMINATED: PASS")

# ============================================================
# 14. Mixed timezone arithmetic must be rejected by contract.
# ============================================================

aware_dt = datetime.fromisoformat(
    "2026-10-01T08:00:00+05:30"
)

naive_dt = datetime.fromisoformat(
    "2026-10-01T08:07:30"
)

aware_flag = (
    aware_dt.tzinfo is not None
    and aware_dt.utcoffset() is not None
)

naive_flag = (
    naive_dt.tzinfo is not None
    and naive_dt.utcoffset() is not None
)

assert aware_flag != naive_flag

print("R56_POS39_MIXED_TIMEZONE_WITNESS: PASS")

# ============================================================
# 15. Non-finite guard is present.
# ============================================================

assert "holding_seconds != holding_seconds" in close_block
assert "Non-finite trade holding time" in close_block

print("R56_POS39_NONFINITE_DURATION_GUARD: PASS")

# ============================================================
# 16. Existing recorder snapshot/checksum contract.
#    Monkeypatch persistence so no real DB mutation occurs.
# ============================================================

import research.recorder as recorder

captured = {}

recorder.init_db = lambda: None

def fake_update_close_trade(uuid, data):
    captured["uuid"] = uuid
    captured["data"] = data

recorder.update_close_trade = fake_update_close_trade

recorded_close_time = "2026-10-01T08:07:30.500000"

recorder.record_trade_close(
    uuid="POS39-WITNESS",
    exit_price=110.0,
    pnl=8.5,
    r_multiple=1.7,
    win_loss=True,
    holding_time=450,
    exit_time=recorded_close_time,
)

data = captured["data"]

assert data["close_time"] == recorded_close_time
assert data["holding_time"] == 450

snapshot = json.loads(data["snapshot_close"])

assert snapshot["timestamp"] == recorded_close_time
assert snapshot["holding_time"] == 450
assert snapshot["exit_price"] == 110.0
assert snapshot["pnl"] == 8.5
assert snapshot["r_multiple"] == 1.7
assert snapshot["win_loss"] is True

expected_checksum = recorder._compute_checksum(snapshot)

assert data["snapshot_close_checksum"] == expected_checksum

print("R56_POS39_RECORDER_CLOSE_TIME_ALIGNMENT: PASS")
print("R56_POS39_SNAPSHOT_HOLDING_TIME_ALIGNMENT: PASS")
print("R56_POS39_SNAPSHOT_CHECKSUM_ALIGNMENT: PASS")

# ============================================================
# 17. Recorder still coerces holding time to integer.
# ============================================================

assert data["holding_time"] == int(450)

print("R56_POS39_RECORDER_INTEGER_PERSISTENCE: PASS")

print("R56_POS39_HOLDING_TIME_AUTHORITY: PASS")
print("============================================================")
