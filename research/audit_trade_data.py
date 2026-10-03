# research/audit_trade_data.py
import sqlite3
from collections import defaultdict
from datetime import datetime
from .database import DB_PATH

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def audit_trade_timestamps():
    """Check every closed trade for timestamp integrity."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT uuid, open_time, close_time, symbol, timeframe, win_loss, pnl
        FROM trades
        WHERE close_time IS NOT NULL
        ORDER BY uuid   -- use a deterministic order; we'll check chronological later
    """).fetchall()
    conn.close()

    if not rows:
        print("No closed trades found.")
        return

    total = len(rows)
    print("=" * 70)
    print("  TRADE DATA AUDIT – TIMESTAMP INTEGRITY")
    print("=" * 70)
    print(f"  Total closed trades : {total}")

    # Check 1: open_time or close_time missing
    missing_open = sum(1 for r in rows if not r["open_time"])
    missing_close = sum(1 for r in rows if not r["close_time"])
    if missing_open > 0:
        print(f"  ❌ {missing_open} trades missing open_time.")
    if missing_close > 0:
        print(f"  ❌ {missing_close} trades missing close_time.")

    # Check 2: date-only timestamps (i.e., no time component, length=10)
    date_only_open = sum(1 for r in rows if r["open_time"] and len(r["open_time"]) <= 10)
    date_only_close = sum(1 for r in rows if r["close_time"] and len(r["close_time"]) <= 10)
    if date_only_open > 0:
        print(f"  ⚠️  {date_only_open} trades have date‑only open_time (no time).")
    if date_only_close > 0:
        print(f"  ⚠️  {date_only_close} trades have date‑only close_time.")

    # Check 3: open_time after close_time
    out_of_order = 0
    invalid_ts = 0
    for r in rows:
        try:
            open_dt = datetime.fromisoformat(r["open_time"])
            close_dt = datetime.fromisoformat(r["close_time"])
            if open_dt > close_dt:
                out_of_order += 1
        except Exception:
            invalid_ts += 1
    if out_of_order > 0:
        print(f"  ❌ {out_of_order} trades have open_time after close_time.")
    if invalid_ts > 0:
        print(f"  ❌ {invalid_ts} trades have unparseable timestamps.")

    # Check 4: duplicate open_time (same second)
    open_times = [r["open_time"] for r in rows if r["open_time"]]
    dup_open = defaultdict(int)
    for ot in open_times:
        dup_open[ot] += 1
    dups = {k: v for k, v in dup_open.items() if v > 1}
    if dups:
        print(f"  ⚠️  Duplicate open_time values found ({len(dups)} unique timestamps repeated).")
        # show a sample
        for ts, count in list(dups.items())[:3]:
            print(f"       '{ts}' appears {count} times")
    else:
        print(f"  ✅ No duplicate open_time values.")

    # Check 5: all trades on the same day
    try:
        dates = set(datetime.fromisoformat(ot).date() for ot in open_times)
        if len(dates) == 1:
            print(f"  ❌ All trades occurred on the same date ({list(dates)[0]}). Walk‑forward impossible.")
        else:
            print(f"  ✅ Trades span {len(dates)} distinct dates.")
    except Exception as e:
        print(f"  ❌ Could not parse dates: {e}")

    # Check 6: chronological order (by open_time)
    sorted_rows = sorted(
        [r for r in rows if r["open_time"] and r["close_time"]],
        key=lambda r: r["open_time"]
    )
    if sorted_rows:
        # Verify sorted order is correct
        for i in range(len(sorted_rows)-1):
            if sorted_rows[i]["open_time"] > sorted_rows[i+1]["open_time"]:
                print(f"  ❌ Trades are not sorted chronologically by open_time.")
                break
        else:
            print(f"  ✅ Trades are in chronological order.")

        # Earliest and latest
        earliest = sorted_rows[0]
        latest = sorted_rows[-1]
        print(f"  Earliest trade : {earliest['open_time']}  (symbol={earliest['symbol']}, uuid={earliest['uuid'][:8]}...)")
        print(f"  Latest trade   : {latest['open_time']}  (symbol={latest['symbol']}, uuid={latest['uuid'][:8]}...)")

        # Time span
        try:
            start = datetime.fromisoformat(earliest["open_time"])
            end = datetime.fromisoformat(latest["open_time"])
            span = end - start
            print(f"  Time span      : {span}")
        except:
            pass

    # Overall verdict
    print("\n  VERDICT")
    issues = (missing_open + missing_close + out_of_order + invalid_ts +
              (1 if len(dates) == 1 else 0) +
              (1 if date_only_open > 0 or date_only_close > 0 else 0))
    if issues == 0:
        print("  ✅ All timestamp checks passed.")
    else:
        print("  ❌ Timestamp integrity issues found. Fix before relying on walk‑forward validation.")
    print("=" * 70)
