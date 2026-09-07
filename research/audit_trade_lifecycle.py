# research/audit_trade_lifecycle.py
import sqlite3
import os
from datetime import datetime
from .database import DB_PATH

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def audit_trade_lifecycle():
    db_abs = os.path.abspath(DB_PATH)
    print("=" * 70)
    print("  TRADE LIFECYCLE AUDIT")
    print("=" * 70)
    print(f"  Database path : {db_abs}")

    conn = get_connection()
    # Check if tables exist
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('trades','score_log','research_runs')").fetchall()
    table_names = [r["name"] for r in tables]
    if "trades" not in table_names:
        print("  ❌ 'trades' table missing. No lifecycle data available.")
        conn.close()
        return

    # Counts
    total_rows = conn.execute("SELECT COUNT(*) as cnt FROM trades").fetchone()["cnt"]
    open_trades = conn.execute("SELECT COUNT(*) as cnt FROM trades WHERE entry_price IS NOT NULL AND close_time IS NULL").fetchone()["cnt"]
    closed_trades = conn.execute("SELECT COUNT(*) as cnt FROM trades WHERE close_time IS NOT NULL").fetchone()["cnt"]
    # Trades that have entry_price but no close_time are "open"
    # Trades that have close_time are "closed"
    # Trades that have both NULL entry_price and NULL close_time should not exist (but we check)
    invalid = conn.execute("SELECT COUNT(*) as cnt FROM trades WHERE entry_price IS NULL AND close_time IS NULL").fetchone()["cnt"]

    print(f"  Total trade rows      : {total_rows}")
    print(f"  Open trades (not yet closed) : {open_trades}")
    print(f"  Closed trades         : {closed_trades}")
    if invalid > 0:
        print(f"  ⚠️  {invalid} rows with no entry_price and no close_time (invalid).")

    # If no closed trades, explain why
    if closed_trades == 0:
        print("\n  ❌ No closed trades found.")
        if open_trades > 0:
            print("  Trade lifecycle stopped after opening but before closing.")
            print("  Possible causes:")
            print("    - Campaign was aborted before backtest completed.")
            print("    - Record-keeping error in the backtest engine.")
        elif total_rows == 0:
            print("  No trades were ever recorded. Run a research campaign first.")
        else:
            print("  Trades exist but none have a close_time. Check backtest engine's trade close logic.")
        conn.close()
        return

    # Timestamp integrity: for every closed trade, verify open_time < close_time
    out_of_order = 0
    missing_open = 0
    missing_close = 0
    rows = conn.execute("""
        SELECT uuid, open_time, close_time
        FROM trades
        WHERE close_time IS NOT NULL
    """).fetchall()
    for r in rows:
        if not r["open_time"]:
            missing_open += 1
            continue
        if not r["close_time"]:
            missing_close += 1
            continue
        try:
            open_dt = datetime.fromisoformat(r["open_time"])
            close_dt = datetime.fromisoformat(r["close_time"])
            if open_dt > close_dt:
                out_of_order += 1
        except Exception:
            pass

    if missing_open > 0:
        print(f"  ⚠️  {missing_open} closed trades missing open_time.")
    if missing_close > 0:
        print(f"  ⚠️  {missing_close} closed trades missing close_time.")
    if out_of_order > 0:
        print(f"  ❌ {out_of_order} closed trades have open_time after close_time.")
    if missing_open == 0 and missing_close == 0 and out_of_order == 0:
        print("  ✅ All closed trades have valid timestamps and open < close.")

    # Check if open trades are stale (open_time older than e.g., 1 hour ago could indicate abandoned)
    if open_trades > 0:
        stale = 0
        now = datetime.now()
        open_rows = conn.execute("SELECT uuid, open_time FROM trades WHERE close_time IS NULL AND open_time IS NOT NULL").fetchall()
        for r in open_rows:
            try:
                open_dt = datetime.fromisoformat(r["open_time"])
                if (now - open_dt).total_seconds() > 3600:
                    stale += 1
            except:
                pass
        if stale > 0:
            print(f"  ⚠️  {stale} open trades are older than 1 hour – they may be abandoned.")

    conn.close()

    # Final verdict
    print("\n  VERDICT")
    if closed_trades > 0 and out_of_order == 0 and missing_open == 0 and missing_close == 0:
        print("  ✅ Trade lifecycle appears consistent and complete.")
    else:
        print("  ❌ Trade lifecycle has issues. Review the findings above.")
    print("=" * 70)
