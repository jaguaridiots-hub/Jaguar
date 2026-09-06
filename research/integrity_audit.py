# research/integrity_audit.py
import sqlite3
from .database import DB_PATH

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def audit_run(run_id):
    """
    Perform integrity checks for a specific research campaign.
    Prints a report of PASS/WARN/FAIL.
    """
    conn = get_connection()
    c = conn.cursor()

    print(f"\n{'='*60}")
    print(f"  INTEGRITY AUDIT – Run ID: {run_id}")
    print(f"{'='*60}")

    # 1. Counts reconciliation between research_runs, trades, and score_log
    c.execute("SELECT * FROM research_runs WHERE run_id = ?", (run_id,))
    run = c.fetchone()
    if not run:
        print("  ❌ Run ID not found in research_runs.")
        return

    run_total_dec = run["total_decisions"]
    run_exec_trades = run["executed_trades"]
    run_wins = run["wins"]
    run_losses = run["losses"]

    # score_log counts – aliased as cnt
    c.execute("SELECT COUNT(*) as cnt FROM score_log WHERE run_id = ?", (run_id,))
    score_total = c.fetchone()["cnt"]

    c.execute("SELECT COUNT(*) as cnt FROM score_log WHERE run_id = ? AND decision IN ('BUY','SELL')", (run_id,))
    score_buy_sell = c.fetchone()["cnt"]

    # trades counts
    c.execute("SELECT COUNT(*) as cnt FROM trades WHERE run_id = ? AND entry_price IS NOT NULL", (run_id,))
    trades_executed = c.fetchone()["cnt"]

    c.execute("SELECT COUNT(*) as cnt FROM trades WHERE run_id = ? AND win_loss = 1", (run_id,))
    trades_wins = c.fetchone()["cnt"]
    c.execute("SELECT COUNT(*) as cnt FROM trades WHERE run_id = ? AND win_loss = 0", (run_id,))
    trades_losses = c.fetchone()["cnt"]

    # Reconciliation
    passed = True
    if score_total != run_total_dec:
        print(f"  ⚠️  Score log total ({score_total}) ≠ research_runs.total_decisions ({run_total_dec})")
        passed = False
    if trades_executed != run_exec_trades:
        print(f"  ⚠️  Trades executed ({trades_executed}) ≠ research_runs.executed_trades ({run_exec_trades})")
        passed = False
    if trades_wins != run_wins:
        print(f"  ⚠️  Trades wins ({trades_wins}) ≠ research_runs.wins ({run_wins})")
        passed = False
    if trades_losses != run_losses:
        print(f"  ⚠️  Trades losses ({trades_losses}) ≠ research_runs.losses ({run_losses})")
        passed = False
    if passed:
        print("  ✅ research_runs counts match trades & score_log")

    # 2. Every BUY/SELL decision maps to at most one trade (no duplicate trade_uuid)
    c.execute("""
        SELECT decision_id, trade_uuid, COUNT(*) as cnt
        FROM score_log
        WHERE run_id = ? AND decision IN ('BUY','SELL')
        GROUP BY trade_uuid
        HAVING cnt > 1
    """, (run_id,))
    dupes = c.fetchall()
    if dupes:
        print(f"  ❌ Duplicate BUY/SELL decisions mapping to same trade_uuid: {len(dupes)} instances")
        passed = False
    else:
        print("  ✅ No duplicate trade_uuid in score_log for BUY/SELL")

    # 3. Every executed trade references an existing score_log decision_id via trade_uuid
    c.execute("""
        SELECT t.uuid, t.run_id
        FROM trades t
        LEFT JOIN score_log s ON t.uuid = s.trade_uuid AND s.run_id = t.run_id
        WHERE t.run_id = ? AND t.entry_price IS NOT NULL AND s.decision_id IS NULL
    """, (run_id,))
    orphan_trades = c.fetchall()
    if orphan_trades:
        print(f"  ❌ Executed trades missing score_log link: {len(orphan_trades)}")
        passed = False
    else:
        print("  ✅ All executed trades have a corresponding score_log decision")

    # 4. New Phase 33D fields completeness (only for new recorder runs)
    c.execute("""
        SELECT COUNT(*) as cnt
        FROM score_log
        WHERE run_id = ? AND (rejection_stage IS NOT NULL OR validator_approved IS NOT NULL)
    """, (run_id,))
    any_new = c.fetchone()["cnt"] > 0

    if any_new:
        print("  ℹ️  New fields detected, checking completeness...")

        missing_rejection_stage = c.execute(
            "SELECT COUNT(*) as cnt FROM score_log WHERE run_id = ? AND rejection_stage IS NULL", (run_id,)
        ).fetchone()["cnt"]

        missing_validator = c.execute(
            "SELECT COUNT(*) as cnt FROM score_log WHERE run_id = ? AND validator_approved IS NULL", (run_id,)
        ).fetchone()["cnt"]

        missing_reasons = c.execute(
            "SELECT COUNT(*) as cnt FROM score_log WHERE run_id = ? AND decision IN ('REJECT','WAIT') AND rejection_reasons IS NULL",
            (run_id,)
        ).fetchone()["cnt"]

        missing_threshold = c.execute(
            "SELECT COUNT(*) as cnt FROM score_log WHERE run_id = ? AND rejection_stage = 'EXECUTION' AND threshold_required_score IS NULL",
            (run_id,)
        ).fetchone()["cnt"]

        missing_snapshot = c.execute(
            "SELECT COUNT(*) as cnt FROM score_log WHERE run_id = ? AND engine_snapshot_json IS NULL", (run_id,)
        ).fetchone()["cnt"]

        missing_mtf = c.execute(
            "SELECT COUNT(*) as cnt FROM score_log WHERE run_id = ? AND mtf_loaded IS NULL", (run_id,)
        ).fetchone()["cnt"]

        if missing_rejection_stage > 0:
            print(f"  ⚠️  {missing_rejection_stage} decisions missing rejection_stage")
            passed = False
        if missing_validator > 0:
            print(f"  ⚠️  {missing_validator} decisions missing validator_approved")
            passed = False
        if missing_reasons > 0:
            print(f"  ⚠️  {missing_reasons} rejected decisions missing rejection_reasons")
            passed = False
        if missing_threshold > 0:
            print(f"  ⚠️  {missing_threshold} EXECUTION rejections missing threshold_required_score")
            passed = False
        if missing_snapshot > 0:
            print(f"  ⚠️  {missing_snapshot} decisions missing engine_snapshot_json")
            passed = False
        if missing_mtf > 0:
            print(f"  ⚠️  {missing_mtf} decisions missing mtf_loaded")
            passed = False
        if all(v == 0 for v in [missing_rejection_stage, missing_validator, missing_reasons, missing_threshold, missing_snapshot, missing_mtf]):
            print("  ✅ All new Phase 33D fields populated correctly")
    else:
        print("  ℹ️  Legacy data – new fields absent, skipping completeness check (expected).")

    # 5. Consistency of BUY/SELL decision count vs executed trades + EXECUTION stage
    c.execute("SELECT COUNT(*) as cnt FROM score_log WHERE run_id = ? AND rejection_stage = 'EXECUTION'", (run_id,))
    exec_rej = c.fetchone()["cnt"]
    expected_trades = score_buy_sell - exec_rej
    if expected_trades != trades_executed:
        print(f"  ⚠️  BUY/SELL decisions ({score_buy_sell}) minus EXECUTION rejections ({exec_rej}) = {expected_trades}, but executed trades = {trades_executed}")
        passed = False
    else:
        print("  ✅ BUY/SELL count reconciles with executed trades + EXECUTION rejections")

    if passed:
        print(f"\n  ✅ AUDIT PASSED for {run_id}")
    else:
        print(f"\n  ❌ AUDIT FAILED – investigate warnings above.")
    conn.close()
