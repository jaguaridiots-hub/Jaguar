# research/evidence_calibration.py
import sqlite3
import json
from collections import defaultdict
from .database import DB_PATH

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ----------------------------------------------------------------------
# Data fetching
# ----------------------------------------------------------------------
def fetch_trade_data():
    """Fetch closed trades with score_log data."""
    conn = get_connection()
    query = """
        SELECT t.win_loss, t.pnl, t.r_multiple, t.holding_time,
               s.brain_score, s.composite_score, s.regime, s.session_score,
               s.contributions_json, s.rejection_reasons, s.rejection_stage,
               s.decision, s.mode, s.timeframe, s.symbol
        FROM trades t
        JOIN score_log s ON t.uuid = s.trade_uuid
        WHERE t.close_time IS NOT NULL
    """
    rows = conn.execute(query).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def fetch_all_decisions():
    """Fetch all decisions (including non-traded) for rejection analysis."""
    conn = get_connection()
    query = """
        SELECT decision, rejection_reasons, brain_score, composite_score,
               regime, session_score, mode, timeframe, symbol
        FROM score_log
    """
    rows = conn.execute(query).fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def compute_metrics(trades):
    """Return win_rate, profit_factor, expectancy, avg_r, total_trades."""
    total = len(trades)
    if total == 0:
        return None, None, None, None, 0
    wins = sum(1 for t in trades if t["win_loss"] == 1)
    losses = total - wins
    win_rate = (wins / total * 100) if total else 0
    gross_profit = sum(t["pnl"] for t in trades if t["pnl"] and t["pnl"] > 0)
    gross_loss = abs(sum(t["pnl"] for t in trades if t["pnl"] and t["pnl"] < 0))
    profit_factor = gross_profit / gross_loss if gross_loss else float('inf')
    avg_win_pnl = gross_profit / wins if wins else 0
    avg_loss_pnl = gross_loss / losses if losses else 0
    expectancy = (wins/total * avg_win_pnl) - (losses/total * avg_loss_pnl) if total else 0
    avg_r = sum(t["r_multiple"] for t in trades if t["r_multiple"] is not None) / total if total else 0
    return win_rate, profit_factor, expectancy, avg_r, total

# ----------------------------------------------------------------------
# 1. Score Calibration
# ----------------------------------------------------------------------
def score_calibration(trades):
    """Analyze win rate etc. for brain and composite score bins."""
    bins = [(0,20), (20,40), (40,60), (60,80), (80,101)]
    brain_report = {}
    comp_report = {}
    for lo, hi in bins:
        brain_sub = [t for t in trades if t["brain_score"] is not None and lo <= t["brain_score"] < hi]
        comp_sub = [t for t in trades if t["composite_score"] is not None and lo <= t["composite_score"] < hi]
        brain_report[f"{lo}-{hi}"] = compute_metrics(brain_sub)
        comp_report[f"{lo}-{hi}"] = compute_metrics(comp_sub)
    return brain_report, comp_report

# ----------------------------------------------------------------------
# 2. Engine Predictive Value
# ----------------------------------------------------------------------
def engine_predictive_value(trades):
    """Calculate predictive metrics per engine."""
    engine_stats = defaultdict(lambda: {
        "pos_wins": 0, "pos_total": 0, "neg_wins": 0, "neg_total": 0,
        "contributions": [], "pnls": [], "r_multiples": []
    })
    for t in trades:
        contribs = json.loads(t["contributions_json"]) if t["contributions_json"] else []
        outcome = t["win_loss"]  # 1=win,0=loss
        pnl = t["pnl"] or 0
        r = t["r_multiple"] or 0
        for eng in contribs:
            name = eng.get("engine") or eng.get("label") or "Unknown"
            contrib = eng.get("contribution", 0)
            engine_stats[name]["contributions"].append(contrib)
            engine_stats[name]["pnls"].append(pnl)
            engine_stats[name]["r_multiples"].append(r)
            if contrib > 0:
                engine_stats[name]["pos_total"] += 1
                if outcome == 1:
                    engine_stats[name]["pos_wins"] += 1
            elif contrib < 0:
                engine_stats[name]["neg_total"] += 1
                if outcome == 1:
                    engine_stats[name]["neg_wins"] += 1

    result = {}
    for eng, stats in engine_stats.items():
        avg_contrib = sum(stats["contributions"]) / len(stats["contributions"]) if stats["contributions"] else 0
        pos_total = stats["pos_total"]
        neg_total = stats["neg_total"]
        pos_wr = (stats["pos_wins"] / pos_total * 100) if pos_total > 0 else None
        neg_wr = (stats["neg_wins"] / neg_total * 100) if neg_total > 0 else None
        # Profit factor for positive/negative contributions
        def pf(subset):
            profit = sum(p for p in subset if p > 0)
            loss = abs(sum(p for p in subset if p < 0))
            return profit/loss if loss else float('inf')
        pos_pf = pf(stats["pnls"][i] for i in range(len(stats["pnls"])) if stats["contributions"][i] > 0)
        neg_pf = pf(stats["pnls"][i] for i in range(len(stats["pnls"])) if stats["contributions"][i] < 0)
        # Expectancy: average pnl per trade for pos/neg
        pos_pnls = [stats["pnls"][i] for i in range(len(stats["pnls"])) if stats["contributions"][i] > 0]
        neg_pnls = [stats["pnls"][i] for i in range(len(stats["pnls"])) if stats["contributions"][i] < 0]
        pos_expect = sum(pos_pnls)/len(pos_pnls) if pos_pnls else 0
        neg_expect = sum(neg_pnls)/len(neg_pnls) if neg_pnls else 0
        # Correlation with wins (point-biserial not really, but we can just use contribution vs win_loss)
        # We'll compute the win rate difference as a proxy.
        wr_diff = (pos_wr - neg_wr) if pos_wr is not None and neg_wr is not None else None
        result[eng] = {
            "avg_contribution": avg_contrib,
            "pos_win_rate": pos_wr,
            "neg_win_rate": neg_wr,
            "pos_profit_factor": pos_pf if pos_total > 0 else None,
            "neg_profit_factor": neg_pf if neg_total > 0 else None,
            "pos_expectancy": pos_expect,
            "neg_expectancy": neg_expect,
            "wr_difference": wr_diff,
            "pos_count": pos_total,
            "neg_count": neg_total
        }
    # Rank by absolute wr_difference
    ranked = sorted(result.items(), key=lambda x: abs(x[1]["wr_difference"]) if x[1]["wr_difference"] is not None else 0, reverse=True)
    return ranked

# ----------------------------------------------------------------------
# 3. Rejection Analysis
# ----------------------------------------------------------------------
def rejection_analysis(all_decisions):
    """Analyze rejection reasons and their impact on trade outcomes (if they had been taken).
    Since we only have outcomes for executed trades, we cannot know if a rejected decision would have been a win/loss.
    Instead, we analyze the distribution of scores and contributions for rejected decisions."""
    # We'll summarize rejection reasons frequency and average scores for each reason.
    reason_stats = defaultdict(lambda: {"count": 0, "brain_scores": [], "composite_scores": []})
    for d in all_decisions:
        if d["decision"] not in ("BUY", "SELL"):
            reasons = []
            if d.get("rejection_reasons"):
                try:
                    reasons = json.loads(d["rejection_reasons"])
                except:
                    reasons = []
            for r in reasons:
                reason_stats[r]["count"] += 1
                if d["brain_score"] is not None:
                    reason_stats[r]["brain_scores"].append(d["brain_score"])
                if d["composite_score"] is not None:
                    reason_stats[r]["composite_scores"].append(d["composite_score"])
    # Compute avg scores per reason
    result = {}
    for reason, data in reason_stats.items():
        avg_brain = sum(data["brain_scores"])/len(data["brain_scores"]) if data["brain_scores"] else None
        avg_comp = sum(data["composite_scores"])/len(data["composite_scores"]) if data["composite_scores"] else None
        result[reason] = {
            "count": data["count"],
            "avg_brain_score": avg_brain,
            "avg_composite_score": avg_comp
        }
    # Sort by count
    return dict(sorted(result.items(), key=lambda x: x[1]["count"], reverse=True))

# ----------------------------------------------------------------------
# 4. Threshold Simulation
# ----------------------------------------------------------------------
def threshold_simulation(trades, score_type="brain", steps=5):
    """Simulate varying thresholds for brain or composite score."""
    scores = [t[f"{score_type}_score"] for t in trades if t[f"{score_type}_score"] is not None]
    if not scores:
        return []
    min_score = int(min(scores))
    max_score = int(max(scores))
    step = max(1, (max_score - min_score) // steps)
    thresholds = list(range(min_score, max_score, step)) + [max_score]
    results = []
    for thresh in thresholds:
        subset = [t for t in trades if t[f"{score_type}_score"] is not None and t[f"{score_type}_score"] >= thresh]
        wr, pf, exp, avg_r, total = compute_metrics(subset)
        results.append({
            "threshold": thresh,
            "trades": total,
            "win_rate": wr,
            "profit_factor": pf,
            "expectancy": exp,
            "avg_r": avg_r
        })
    return results

# ----------------------------------------------------------------------
# 5. Combination Analysis
# ----------------------------------------------------------------------
def combination_analysis(trades):
    """Find best combinations of regime, session (using score_log session_score bucketed), timeframe, brain/composite score ranges."""
    # Bucket session_score
    def bucket_session(score):
        if score is None: return "unknown"
        if score < 10: return "low"
        if score < 20: return "medium"
        return "high"
    combos = defaultdict(list)
    for t in trades:
        regime = t["regime"] or "UNKNOWN"
        session = bucket_session(t["session_score"])
        timeframe = t["timeframe"]
        brain = t["brain_score"]
        comp = t["composite_score"]
        if brain is None or comp is None: continue
        brain_bucket = f"{brain//20*20}-{brain//20*20+20}" if brain < 80 else "80-100"
        comp_bucket = f"{comp//20*20}-{comp//20*20+20}" if comp < 80 else "80-100"
        key = f"{regime}|{session}|{timeframe}|{brain_bucket}|{comp_bucket}"
        combos[key].append(t)
    combo_metrics = {}
    for combo, sub_trades in combos.items():
        wr, pf, exp, avg_r, total = compute_metrics(sub_trades)
        combo_metrics[combo] = {
            "trades": total,
            "win_rate": wr,
            "profit_factor": pf,
            "expectancy": exp,
            "avg_r": avg_r
        }
    # Sort by expectancy descending
    return dict(sorted(combo_metrics.items(), key=lambda x: x[1]["expectancy"] if x[1]["expectancy"] else 0, reverse=True))

# ----------------------------------------------------------------------
# 6. Predictive Quality
# ----------------------------------------------------------------------
def predictive_quality(trades):
    """Measure separation between winners and losers for brain and composite scores."""
    winners = [t for t in trades if t["win_loss"] == 1]
    losers = [t for t in trades if t["win_loss"] == 0]
    def stats(subset):
        scores = [t["brain_score"] for t in subset if t["brain_score"] is not None]
        if not scores: return None
        return sum(scores)/len(scores), min(scores), max(scores)
    win_brain = stats(winners)
    loss_brain = stats(losers)
    win_comp = stats([t for t in winners if t["composite_score"] is not None])
    loss_comp = stats([t for t in losers if t["composite_score"] is not None])
    # Overlap: simple heuristic, see if means differ significantly
    return {
        "winner_brain_mean": win_brain[0] if win_brain else None,
        "loser_brain_mean": loss_brain[0] if loss_brain else None,
        "winner_comp_mean": win_comp[0] if win_comp else None,
        "loser_comp_mean": loss_comp[0] if loss_comp else None,
    }

# ----------------------------------------------------------------------
# Report Generation
# ----------------------------------------------------------------------
def print_calibration_report():
    trades = fetch_trade_data()
    all_decisions = fetch_all_decisions()
    if not trades:
        print("No closed trades found.")
        return

    print("=" * 70)
    print("  JAGUAR QUANT X – EVIDENCE CALIBRATION & PREDICTIVE OPTIMIZATION REPORT")
    print("=" * 70)

    # 1. Score Calibration
    print("\n[1] SCORE CALIBRATION")
    brain_bins, comp_bins = score_calibration(trades)
    print("\n  Brain Score Ranges:")
    for rng, (wr, pf, exp, avg_r, cnt) in brain_bins.items():
        if cnt == 0:
            print(f"    {rng:8s}: No trades")
        else:
            print(f"    {rng:8s}: Trades={cnt:5d} | WR={wr:.1f}% | PF={pf:.2f} | Expect={exp:.2f} | AvgR={avg_r:.2f}")
    print("\n  Composite Score Ranges:")
    for rng, (wr, pf, exp, avg_r, cnt) in comp_bins.items():
        if cnt == 0:
            print(f"    {rng:8s}: No trades")
        else:
            print(f"    {rng:8s}: Trades={cnt:5d} | WR={wr:.1f}% | PF={pf:.2f} | Expect={exp:.2f} | AvgR={avg_r:.2f}")

    # 2. Engine Predictive Value
    print("\n[2] ENGINE PREDICTIVE VALUE")
    engines = engine_predictive_value(trades)
    print(f"\n  {'Engine':25s} {'AvgContrib':>10s} {'PosWR':>8s} {'NegWR':>8s} {'PosPF':>8s} {'NegPF':>8s} {'PosCnt':>8s} {'NegCnt':>8s} {'WR Diff':>8s}")
    for eng, data in engines:
        name = eng
        avg_contrib = data["avg_contribution"]
        pos_wr = f"{data['pos_win_rate']:.1f}%" if data['pos_win_rate'] is not None else "N/A"
        neg_wr = f"{data['neg_win_rate']:.1f}%" if data['neg_win_rate'] is not None else "N/A"
        pos_pf = f"{data['pos_profit_factor']:.2f}" if data['pos_profit_factor'] is not None else "N/A"
        neg_pf = f"{data['neg_profit_factor']:.2f}" if data['neg_profit_factor'] is not None else "N/A"
        pos_cnt = data["pos_count"]
        neg_cnt = data["neg_count"]
        wr_diff = f"{data['wr_difference']:+.1f}%" if data['wr_difference'] is not None else "N/A"
        print(f"  {name:25s} {avg_contrib:>+10.2f} {pos_wr:>8s} {neg_wr:>8s} {pos_pf:>8s} {neg_pf:>8s} {pos_cnt:>8d} {neg_cnt:>8d} {wr_diff:>8s}")

    # 3. Rejection Analysis
    print("\n[3] REJECTION ANALYSIS")
    rejections = rejection_analysis(all_decisions)
    if rejections:
        print(f"\n  {'Reason':50s} {'Count':>6s} {'Avg Brain':>10s} {'Avg Comp':>10s}")
        for reason, data in rejections.items():
            avg_b = f"{data['avg_brain_score']:.1f}" if data['avg_brain_score'] else "N/A"
            avg_c = f"{data['avg_composite_score']:.1f}" if data['avg_composite_score'] else "N/A"
            print(f"  {reason:50s} {data['count']:>6d} {avg_b:>10s} {avg_c:>10s}")
    else:
        print("  No rejection reasons recorded.")

    # 4. Threshold Simulation
    print("\n[4] THRESHOLD SIMULATION")
    # Brain
    print("\n  Brain Score Thresholds:")
    brain_sim = threshold_simulation(trades, "brain", steps=5)
    if brain_sim:
        print(f"    {'Thresh':>6s} {'Trades':>7s} {'WR':>8s} {'PF':>8s} {'Expect':>8s} {'AvgR':>8s}")
        for s in brain_sim:
            wr = f"{s['win_rate']:.1f}%" if s['win_rate'] else "N/A"
            pf = f"{s['profit_factor']:.2f}" if s['profit_factor'] else "N/A"
            exp = f"{s['expectancy']:.2f}" if s['expectancy'] else "N/A"
            avg_r = f"{s['avg_r']:.2f}" if s['avg_r'] else "N/A"
            print(f"    {s['threshold']:>6d} {s['trades']:>7d} {wr:>8s} {pf:>8s} {exp:>8s} {avg_r:>8s}")
    else:
        print("    No brain score data.")
    # Composite
    print("\n  Composite Score Thresholds:")
    comp_sim = threshold_simulation(trades, "composite", steps=5)
    if comp_sim:
        print(f"    {'Thresh':>6s} {'Trades':>7s} {'WR':>8s} {'PF':>8s} {'Expect':>8s} {'AvgR':>8s}")
        for s in comp_sim:
            wr = f"{s['win_rate']:.1f}%" if s['win_rate'] else "N/A"
            pf = f"{s['profit_factor']:.2f}" if s['profit_factor'] else "N/A"
            exp = f"{s['expectancy']:.2f}" if s['expectancy'] else "N/A"
            avg_r = f"{s['avg_r']:.2f}" if s['avg_r'] else "N/A"
            print(f"    {s['threshold']:>6d} {s['trades']:>7d} {wr:>8s} {pf:>8s} {exp:>8s} {avg_r:>8s}")
    else:
        print("    No composite score data.")

    # 5. Combination Analysis (top 10)
    print("\n[5] TOP COMBINATIONS (by expectancy)")
    combos = combination_analysis(trades)
    count = 0
    for combo, metrics in combos.items():
        if count >= 10: break
        wr = f"{metrics['win_rate']:.1f}%" if metrics['win_rate'] else "N/A"
        pf = f"{metrics['profit_factor']:.2f}" if metrics['profit_factor'] else "N/A"
        exp = f"{metrics['expectancy']:.2f}" if metrics['expectancy'] else "N/A"
        print(f"  {combo:60s} Trades={metrics['trades']:4d} WR={wr:>8s} PF={pf:>8s} Expect={exp:>8s}")
        count += 1

    # 6. Predictive Quality
    print("\n[6] PREDICTIVE QUALITY")
    pq = predictive_quality(trades)
    print(f"  Winner Brain Score Mean : {pq['winner_brain_mean']:.2f}" if pq['winner_brain_mean'] else "  Winner Brain Score Mean : N/A")
    print(f"  Loser Brain Score Mean  : {pq['loser_brain_mean']:.2f}" if pq['loser_brain_mean'] else "  Loser Brain Score Mean  : N/A")
    print(f"  Winner Composite Score Mean : {pq['winner_comp_mean']:.2f}" if pq['winner_comp_mean'] else "  Winner Composite Score Mean : N/A")
    print(f"  Loser Composite Score Mean  : {pq['loser_comp_mean']:.2f}" if pq['loser_comp_mean'] else "  Loser Composite Score Mean  : N/A")
    if pq['winner_brain_mean'] and pq['loser_brain_mean']:
        diff = abs(pq['winner_brain_mean'] - pq['loser_brain_mean'])
        if diff < 5:
            print("  ⚠️  Brain score difference is small (<5); limited predictive separation.")
    if pq['winner_comp_mean'] and pq['loser_comp_mean']:
        diff = abs(pq['winner_comp_mean'] - pq['loser_comp_mean'])
        if diff < 5:
            print("  ⚠️  Composite score difference is small (<5); limited predictive separation.")

    # 7. Final Recommendations (simplified, derived from above)
    print("\n[7] FINAL RECOMMENDATIONS")
    # Find best score range by profit factor
    best_brain_range = max(brain_bins.items(), key=lambda x: x[1][1] if x[1][1] is not None else 0)
    best_comp_range = max(comp_bins.items(), key=lambda x: x[1][1] if x[1][1] is not None else 0)
    print(f"  - Optimal Brain Score range: {best_brain_range[0]} (PF={best_brain_range[1][1]:.2f}, WR={best_brain_range[1][0]:.1f}%)")
    print(f"  - Optimal Composite Score range: {best_comp_range[0]} (PF={best_comp_range[1][1]:.2f}, WR={best_comp_range[1][0]:.1f}%)")
    # Engine ranking
    if engines:
        top_engine = engines[0][0]
        print(f"  - Most predictive engine: {top_engine} (largest WR difference)")
        # if any engine has strong negative predictive value
        worst_engine = engines[-1][0]
        print(f"  - Least predictive engine: {worst_engine}")
    else:
        print("  - Not enough data for engine recommendations.")
    # Threshold suggestion
    if brain_sim:
        best_brain_thresh = max(brain_sim, key=lambda x: x["profit_factor"] if x["profit_factor"] else 0)
        print(f"  - Suggested Brain Score threshold: {best_brain_thresh['threshold']} (PF={best_brain_thresh['profit_factor']:.2f}, Trades={best_brain_thresh['trades']})")
    if comp_sim:
        best_comp_thresh = max(comp_sim, key=lambda x: x["profit_factor"] if x["profit_factor"] else 0)
        print(f"  - Suggested Composite Score threshold: {best_comp_thresh['threshold']} (PF={best_comp_thresh['profit_factor']:.2f}, Trades={best_comp_thresh['trades']})")
    # If scores overlap heavily, mention calibration issue
    if pq['winner_brain_mean'] and pq['loser_brain_mean'] and abs(pq['winner_brain_mean'] - pq['loser_brain_mean']) < 5:
        print("  - ⚠️ Brain score shows weak predictive power; consider incorporating additional signal sources.")
    if pq['winner_comp_mean'] and pq['loser_comp_mean'] and abs(pq['winner_comp_mean'] - pq['loser_comp_mean']) < 5:
        print("  - ⚠️ Composite score shows weak predictive power; review weighting and calibration.")

    print("\n" + "=" * 70)
    print("  All recommendations are evidence‑based and read‑only.")
