# research/brain_calibration_report.py
import sqlite3
import json
from collections import defaultdict
from .database import DB_PATH

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def fetch_trades_with_contributions(run_id=None):
    """Return every closed trade with its brain score, outcome, and per-engine contributions, optionally filtered by run_id."""
    conn = get_connection()
    if run_id:
        query = """
            SELECT t.win_loss, t.pnl, s.brain_score, s.contributions_json
            FROM trades t
            JOIN score_log s ON t.uuid = s.trade_uuid
            WHERE t.close_time IS NOT NULL AND s.run_id = ?
        """
        rows = conn.execute(query, (run_id,)).fetchall()
    else:
        query = """
            SELECT t.win_loss, t.pnl, s.brain_score, s.contributions_json
            FROM trades t
            JOIN score_log s ON t.uuid = s.trade_uuid
            WHERE t.close_time IS NOT NULL
        """
        rows = conn.execute(query).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def generate_brain_calibration_report(run_id=None):
    trades = fetch_trades_with_contributions(run_id)
    if not trades:
        print("No closed trades found.")
        return

    engine_contrib_wins = defaultdict(list)
    engine_contrib_losses = defaultdict(list)
    brain_scores_wins = []
    brain_scores_losses = []
    all_brain = []

    for t in trades:
        outcome = "WIN" if t["win_loss"] == 1 else "LOSS"
        brain = t["brain_score"]
        all_brain.append(brain)
        if outcome == "WIN":
            brain_scores_wins.append(brain)
        else:
            brain_scores_losses.append(brain)

        contribs = json.loads(t["contributions_json"]) if t["contributions_json"] else []
        for eng in contribs:
            name = eng.get("engine") or eng.get("label") or "Unknown"
            contrib = eng.get("contribution", 0)
            if outcome == "WIN":
                engine_contrib_wins[name].append(contrib)
            else:
                engine_contrib_losses[name].append(contrib)

    print("=" * 70)
    print("  BRAIN CALIBRATION REPORT")
    if run_id:
        print(f"  Run ID                 : {run_id}")
    print("=" * 70)
    print(f"  Trades analysed        : {len(trades)}")
    print(f"  Brain Score range      : {min(all_brain):.1f} – {max(all_brain):.1f}")
    print(f"  Median Brain Score     : {sorted(all_brain)[len(all_brain)//2]:.1f}")
    high_end = sum(1 for b in all_brain if b >= 90)
    print(f"  Trades with score ≥ 90 : {high_end} ({high_end/len(all_brain)*100:.1f}%)")
    print(f"  Mean Winner Brain Score: {sum(brain_scores_wins)/len(brain_scores_wins):.2f}" if brain_scores_wins else "  Mean Winner Brain Score: N/A")
    print(f"  Mean Loser Brain Score : {sum(brain_scores_losses)/len(brain_scores_losses):.2f}" if brain_scores_losses else "  Mean Loser Brain Score : N/A")

    print("\n  [1] ENGINE CONTRIBUTIONS (Winners vs Losers)")
    all_engines = set(list(engine_contrib_wins.keys()) + list(engine_contrib_losses.keys()))
    for eng in sorted(all_engines):
        win_vals = engine_contrib_wins.get(eng, [])
        loss_vals = engine_contrib_losses.get(eng, [])
        mean_win = sum(win_vals)/len(win_vals) if win_vals else 0
        mean_loss = sum(loss_vals)/len(loss_vals) if loss_vals else 0
        diff = mean_win - mean_loss
        print(f"  {eng:25s}: WinMean={mean_win:+.2f}  LossMean={mean_loss:+.2f}  Diff={diff:+.2f}")

    print("\n  [2] MONOTONICITY CHECK")
    buckets = [(0,20),(20,40),(40,60),(60,80),(80,101)]
    for lo, hi in buckets:
        bucket_trades = [t for t in trades if lo <= t["brain_score"] < hi]
        if not bucket_trades:
            continue
        wins = sum(1 for t in bucket_trades if t["win_loss"] == 1)
        total = len(bucket_trades)
        wr = wins/total*100
        gross_profit = sum(t["pnl"] for t in bucket_trades if t["pnl"] and t["pnl"] > 0)
        gross_loss = abs(sum(t["pnl"] for t in bucket_trades if t["pnl"] and t["pnl"] < 0))
        pf = gross_profit/gross_loss if gross_loss else float('inf')
        print(f"  {lo:3d}-{hi:3d}: Trades={total:4d}  WinRate={wr:.1f}%  PF={pf:.2f}")

    print("\n  [3] PREDICTIVE IMPORTANCE (point-biserial correlation with outcome)")
    engine_corrs = {}
    for eng in sorted(all_engines):
        vals = []
        outcomes = []
        for t in trades:
            contribs = json.loads(t["contributions_json"]) if t["contributions_json"] else []
            for c in contribs:
                if (c.get("engine") or c.get("label")) == eng:
                    vals.append(c.get("contribution", 0))
                    outcomes.append(t["win_loss"])
                    break
        if len(vals) < 10:
            engine_corrs[eng] = "insufficient"
            continue
        try:
            import statistics
            corr = statistics.correlation(vals, outcomes)
        except:
            corr = "constant"
        engine_corrs[eng] = corr

    sorted_engines = sorted(engine_corrs.items(), key=lambda x: abs(x[1]) if isinstance(x[1], (int, float)) else 0, reverse=True)
    for eng, corr in sorted_engines:
        if isinstance(corr, float):
            print(f"  {eng:25s}: r = {corr:+.4f}")
        else:
            print(f"  {eng:25s}: {corr}")

    print("\n  [4] RECOMMENDATIONS")
    if high_end > 0.7 * len(trades):
        print("  ⚠️  Over 70% of trades have Brain Score ≥ 90 – severe score compression.")
        print("      Consider reducing the base Technical Score or capping engine contributions.")
    print("=" * 70)
