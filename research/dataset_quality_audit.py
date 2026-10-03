# research/dataset_quality_audit.py
import sqlite3
import json
from collections import defaultdict
from .database import DB_PATH

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def run_dataset_quality_audit():
    conn = get_connection()
    runs = conn.execute("""
        SELECT run_id, symbols, modes, timeframes, total_decisions,
               executed_trades, wins, losses, start_time, end_time
        FROM research_runs
        WHERE end_time IS NOT NULL
        ORDER BY start_time
    """).fetchall()
    conn.close()

    if not runs:
        print("No completed campaigns found.")
        return

    # Per-campaign stats
    campaign_stats = []
    all_decisions = []  # across all campaigns for overall class/regime stats
    total_trades_overall = 0
    engine_usage = defaultdict(int)  # count of trades where engine contributed non-zero
    total_trades_with_contributions = 0

    for run in runs:
        run_id = run["run_id"]
        sym = run["symbols"]
        mode = run["modes"]
        trades = run["executed_trades"]
        wins = run["wins"]
        losses = run["losses"]
        status = "✅ GOOD" if trades >= 200 else ("⚠️ LOW SAMPLE" if trades > 0 else "❌ NO DATA")
        campaign_stats.append((sym, mode, trades, wins, losses, status))

        # For this campaign, collect engine contributions and regime/decision info
        conn = get_connection()
        # Get closed trades with contributions
        rows = conn.execute("""
            SELECT s.contributions_json, s.decision, s.regime
            FROM trades t
            JOIN score_log s ON t.uuid = s.trade_uuid
            WHERE t.close_time IS NOT NULL AND s.run_id = ?
        """, (run_id,)).fetchall()
        conn.close()

        for row in rows:
            total_trades_overall += 1
            # Engine usage
            contribs = json.loads(row["contributions_json"]) if row["contributions_json"] else []
            for eng in contribs:
                name = eng.get("engine") or eng.get("label") or "Unknown"
                contrib = eng.get("contribution", 0)
                if contrib != 0:
                    engine_usage[name] += 1
            if contribs:  # if we have contributions at all, count the trade
                total_trades_with_contributions += 1

            # Decisions (all decisions, not just trades, but we only have score_log for trades that exist)
            # Actually we have score_log for all decisions, including non-trades. To get class balance we need all decisions.
            # We'll collect separately.

        # For class balance and regime, we query all score_log entries for this run, not just trades
        conn2 = get_connection()
        dec_rows = conn2.execute("""
            SELECT decision, regime FROM score_log WHERE run_id = ?
        """, (run_id,)).fetchall()
        conn2.close()
        for d in dec_rows:
            all_decisions.append((d["decision"], d["regime"]))

    # Overall class balance
    decision_counts = defaultdict(int)
    regime_counts = defaultdict(int)
    total_decisions = len(all_decisions)
    for dec, reg in all_decisions:
        decision_counts[dec] += 1
        if reg:
            regime_counts[reg] += 1

    # Engine coverage (percentage of trades where engine contributed non-zero)
    engine_coverage = {}
    for eng, count in engine_usage.items():
        engine_coverage[eng] = (count / total_trades_with_contributions * 100) if total_trades_with_contributions else 0

    # Print report
    print("=" * 70)
    print("  DATASET QUALITY AUDIT")
    print("=" * 70)

    print("\n  Campaign Performance:")
    print(f"  {'Symbol':10s} {'Mode':8s} {'Trades':>7s} {'Wins':>7s} {'Losses':>7s} {'Status':>15s}")
    print(f"  {'-'*10} {'-'*8} {'-'*7} {'-'*7} {'-'*7} {'-'*15}")
    for sym, mode, trades, wins, losses, status in campaign_stats:
        print(f"  {sym:10s} {mode:8s} {trades:>7d} {wins:>7d} {losses:>7d} {status:>15s}")

    print("\n  Engine Coverage (% of trades where engine contributed ≠ 0):")
    if engine_coverage:
        for eng, cov in sorted(engine_coverage.items(), key=lambda x: x[1], reverse=True):
            print(f"  {eng:25s}: {cov:5.1f}%")
    else:
        print("  No engine contribution data available.")

    print("\n  Class Balance (all decisions across campaigns):")
    for dec in sorted(decision_counts.keys()):
        cnt = decision_counts[dec]
        pct = (cnt / total_decisions * 100) if total_decisions else 0
        print(f"  {dec:10s}: {cnt:6d} ({pct:5.1f}%)")

    print("\n  Regime Distribution (all decisions):")
    if regime_counts:
        for reg, cnt in sorted(regime_counts.items(), key=lambda x: x[1], reverse=True):
            pct = (cnt / total_decisions * 100) if total_decisions else 0
            print(f"  {reg:15s}: {cnt:6d} ({pct:5.1f}%)")
    else:
        print("  No regime data recorded.")

    # Recommendations
    print("\n  Recommendations:")
    missing_swing = any(c[1] == "SWING" and c[2] == 0 for c in campaign_stats)
    missing_btc = any(c[0] == "BTC-USD" and c[2] == 0 for c in campaign_stats)
    low_trend = regime_counts.get("TREND", 0) < total_decisions * 0.1
    bias_scalp = all(c[1] == "SCALP" for c in campaign_stats if c[2] > 0)

    if missing_swing:
        print("  - Need additional SWING campaigns (currently 0 trades).")
    if missing_btc:
        print("  - Need BTC-USD campaigns with trades.")
    if low_trend:
        print("  - Training data is heavily COMPRESSION; add more TREND regime samples.")
    if bias_scalp:
        print("  - Training set is biased toward SCALP; add SWING/CLASSIC campaigns.")
    if not any([missing_swing, missing_btc, low_trend, bias_scalp]):
        print("  - Dataset appears sufficient and balanced.")
    print("=" * 70)
