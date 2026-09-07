# research/score_discrimination_audit.py
import sqlite3
import json
import statistics
from collections import defaultdict
from .database import DB_PATH

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def fetch_trades():
    """Fetch closed trades with score_log data."""
    conn = get_connection()
    query = """
        SELECT t.win_loss, t.pnl, t.r_multiple, t.holding_time,
               s.brain_score, s.composite_score, s.regime, s.session_score,
               s.contributions_json, s.decision, s.mode, s.timeframe, s.symbol
        FROM trades t
        JOIN score_log s ON t.uuid = s.trade_uuid
        WHERE t.close_time IS NOT NULL
    """
    rows = conn.execute(query).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def fetch_all_decisions():
    """Fetch all decisions with contributions for weight simulation."""
    conn = get_connection()
    query = """
        SELECT decision_id, decision, brain_score, composite_score, contributions_json,
               mode, trade_uuid
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
# 1. Score Discrimination
# ----------------------------------------------------------------------
def score_discrimination(trades):
    winners = [t for t in trades if t["win_loss"] == 1]
    losers = [t for t in trades if t["win_loss"] == 0]
    def stats(subset, key):
        vals = [t[key] for t in subset if t[key] is not None]
        if not vals:
            return None
        return {
            "mean": statistics.mean(vals),
            "stdev": statistics.stdev(vals) if len(vals)>1 else 0,
            "min": min(vals),
            "max": max(vals),
            "median": statistics.median(vals)
        }
    brain_win = stats(winners, "brain_score")
    brain_loss = stats(losers, "brain_score")
    comp_win = stats(winners, "composite_score")
    comp_loss = stats(losers, "composite_score")
    # Overlap ratio (simplified: proportion of range overlap)
    def overlap_ratio(stat1, stat2):
        if not stat1 or not stat2:
            return None
        min1, max1 = stat1["min"], stat1["max"]
        min2, max2 = stat2["min"], stat2["max"]
        if max1 < min2 or max2 < min1:
            return 0.0
        overlap_low = max(min1, min2)
        overlap_high = min(max1, max2)
        total_range = max(max1, max2) - min(min1, min2)
        if total_range == 0:
            return 1.0
        return (overlap_high - overlap_low) / total_range
    brain_overlap = overlap_ratio(brain_win, brain_loss)
    comp_overlap = overlap_ratio(comp_win, comp_loss)
    # Separation score: Cohen's d
    def cohens_d(stat1, stat2):
        if not stat1 or not stat2:
            return None
        n1 = len(winners)
        n2 = len(losers)
        if n1<2 or n2<2:
            return None
        pooled_sd = (((n1-1)*stat1["stdev"]**2 + (n2-1)*stat2["stdev"]**2) / (n1+n2-2))**0.5
        if pooled_sd == 0:
            return 0.0
        return (stat1["mean"] - stat2["mean"]) / pooled_sd
    brain_d = cohens_d(brain_win, brain_loss)
    comp_d = cohens_d(comp_win, comp_loss)
    return {
        "brain_winner": brain_win,
        "brain_loser": brain_loss,
        "composite_winner": comp_win,
        "composite_loser": comp_loss,
        "brain_overlap": brain_overlap,
        "composite_overlap": comp_overlap,
        "brain_cohens_d": brain_d,
        "composite_cohens_d": comp_d
    }

# ----------------------------------------------------------------------
# 2. Engine Contribution Audit
# ----------------------------------------------------------------------
def engine_contribution_audit(trades):
    engines = defaultdict(lambda: {
        "contributions": [], "win_loss": [], "pnls": [], "r_multiples": [],
        "pos_count": 0, "neg_count": 0, "zero_count": 0
    })
    for t in trades:
        contribs = json.loads(t["contributions_json"]) if t["contributions_json"] else []
        wl = t["win_loss"]
        pnl = t["pnl"] or 0
        r = t["r_multiple"] or 0
        for eng in contribs:
            name = eng.get("engine") or eng.get("label") or "Unknown"
            contrib = eng.get("contribution", 0)
            engines[name]["contributions"].append(contrib)
            engines[name]["win_loss"].append(wl)
            engines[name]["pnls"].append(pnl)
            engines[name]["r_multiples"].append(r)
            if contrib > 0: engines[name]["pos_count"] += 1
            elif contrib < 0: engines[name]["neg_count"] += 1
            else: engines[name]["zero_count"] += 1

    audit = {}
    for name, data in engines.items():
        avg_contrib = sum(data["contributions"]) / len(data["contributions"]) if data["contributions"] else 0
        # Win rate when positive vs negative
        pos_wins = sum(1 for i in range(len(data["contributions"])) if data["contributions"][i] > 0 and data["win_loss"][i] == 1)
        neg_wins = sum(1 for i in range(len(data["contributions"])) if data["contributions"][i] < 0 and data["win_loss"][i] == 1)
        pos_total = data["pos_count"]
        neg_total = data["neg_count"]
        pos_wr = (pos_wins/pos_total*100) if pos_total>0 else None
        neg_wr = (neg_wins/neg_total*100) if neg_total>0 else None
        # Correlation contribution vs win_loss (point-biserial)
        corr = None
        if len(data["contributions"]) >= 3:
            try:
                corr = statistics.correlation(data["contributions"], data["win_loss"])
            except statistics.StatisticsError:
                corr = "constant"
        # Contradictions
        contradictions = []
        if pos_total == 0 and neg_total == 0 and avg_contrib != 0:
            contradictions.append("Non-zero average but no positive/negative samples.")
        audit[name] = {
            "avg_contribution": avg_contrib,
            "pos_count": pos_total,
            "neg_count": neg_total,
            "zero_count": data["zero_count"],
            "pos_win_rate": pos_wr,
            "neg_win_rate": neg_wr,
            "correlation_win_loss": corr,
            "contradictions": contradictions
        }
    return audit

# ----------------------------------------------------------------------
# 3. Predictive Importance (ranking)
# ----------------------------------------------------------------------
def predictive_importance(trades):
    audit = engine_contribution_audit(trades)
    ranking = []
    for name, data in audit.items():
        if data["pos_win_rate"] is not None and data["neg_win_rate"] is not None:
            diff = data["pos_win_rate"] - data["neg_win_rate"]
        else:
            diff = 0.0
        corr_val = 0.0
        if isinstance(data["correlation_win_loss"], (int, float)):
            corr_val = data["correlation_win_loss"]
        score = abs(diff) + abs(corr_val)*10
        ranking.append((name, diff, corr_val, score))
    ranking.sort(key=lambda x: x[3], reverse=True)
    return ranking

# ----------------------------------------------------------------------
# 4. Correlation Analysis
# ----------------------------------------------------------------------
def correlation_analysis(trades):
    brain_scores = [t["brain_score"] for t in trades if t["brain_score"] is not None]
    comp_scores = [t["composite_score"] for t in trades if t["composite_score"] is not None]
    win_loss = [t["win_loss"] for t in trades]
    pnls = [t["pnl"] for t in trades]
    r_multiples = [t["r_multiple"] for t in trades]
    results = {}
    if len(brain_scores) >= 3:
        try:
            results["brain_vs_win"] = statistics.correlation(brain_scores, win_loss)
        except statistics.StatisticsError:
            results["brain_vs_win"] = "constant"
        try:
            results["brain_vs_pnl"] = statistics.correlation(brain_scores, pnls)
        except statistics.StatisticsError:
            results["brain_vs_pnl"] = "constant"
        try:
            results["brain_vs_r"] = statistics.correlation(brain_scores, r_multiples)
        except statistics.StatisticsError:
            results["brain_vs_r"] = "constant"
    else:
        results["brain"] = "insufficient data"
    if len(comp_scores) >= 3:
        try:
            results["composite_vs_win"] = statistics.correlation(comp_scores, win_loss)
        except statistics.StatisticsError:
            results["composite_vs_win"] = "constant"
        try:
            results["composite_vs_pnl"] = statistics.correlation(comp_scores, pnls)
        except statistics.StatisticsError:
            results["composite_vs_pnl"] = "constant"
        try:
            results["composite_vs_r"] = statistics.correlation(comp_scores, r_multiples)
        except statistics.StatisticsError:
            results["composite_vs_r"] = "constant"
    return results

# ----------------------------------------------------------------------
# 5. Weight Sensitivity Simulation
# ----------------------------------------------------------------------
def weight_sensitivity_simulation(all_decisions, trades):
    # Determine mode-specific thresholds
    mode_thresholds = {}
    accepted = [t for t in trades if t["decision"] in ("BUY", "SELL")]
    for t in accepted:
        mode = t["mode"]
        if mode not in mode_thresholds:
            mode_thresholds[mode] = t["composite_score"]
        else:
            if t["composite_score"] < mode_thresholds[mode]:
                mode_thresholds[mode] = t["composite_score"]
    if not mode_thresholds:
        mode_thresholds = {"SCALP": 70, "SWING": 70, "CLASSIC": 50}

    # Preprocess decisions
    decisions = []
    for d in all_decisions:
        if d["brain_score"] is None or d["composite_score"] is None:
            continue
        contribs = json.loads(d["contributions_json"]) if d["contributions_json"] else []
        total_contrib = sum(eng.get("contribution", 0) for eng in contribs)
        base_tech = d["brain_score"] - total_contrib
        comp_offset = d["composite_score"] - d["brain_score"]
        decisions.append({
            "decision_id": d["decision_id"],
            "mode": d["mode"],
            "brain_score": d["brain_score"],
            "composite_score": d["composite_score"],
            "base_tech": base_tech,
            "comp_offset": comp_offset,
            "contributions": contribs,
            "trade_uuid": d["trade_uuid"],
            "decision": d["decision"]
        })

    # Fetch trades with uuid
    conn = get_connection()
    trade_rows = conn.execute("SELECT * FROM trades WHERE close_time IS NOT NULL").fetchall()
    conn.close()
    trade_data = {r["uuid"]: dict(r) for r in trade_rows}

    engine_names = set()
    for d in decisions:
        for eng in d["contributions"]:
            name = eng.get("engine") or eng.get("label") or "Unknown"
            engine_names.add(name)

    multipliers = [0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3]
    results = {}

    for engine in engine_names:
        engine_results = []
        for mult in multipliers:
            simulated_trades = []
            for d in decisions:
                new_brain = d["base_tech"]
                for eng in d["contributions"]:
                    contrib = eng.get("contribution", 0)
                    eng_name = eng.get("engine") or eng.get("label") or "Unknown"
                    if eng_name == engine:
                        new_brain += contrib * mult
                    else:
                        new_brain += contrib
                new_composite = new_brain + d["comp_offset"]
                mode = d["mode"]
                threshold = mode_thresholds.get(mode, 70)
                if new_composite >= threshold:
                    tuuid = d["trade_uuid"]
                    if tuuid and tuuid in trade_data:
                        simulated_trades.append(trade_data[tuuid])
            total = len(simulated_trades)
            if total == 0:
                engine_results.append({"multiplier": mult, "trades": 0, "win_rate": None, "profit_factor": None, "expectancy": None})
                continue
            wins = sum(1 for t in simulated_trades if t["win_loss"] == 1)
            losses = total - wins
            win_rate = (wins / total * 100) if total else 0
            gross_profit = sum(t["pnl"] for t in simulated_trades if t["pnl"] and t["pnl"] > 0)
            gross_loss = abs(sum(t["pnl"] for t in simulated_trades if t["pnl"] and t["pnl"] < 0))
            profit_factor = gross_profit / gross_loss if gross_loss else float('inf')
            avg_win = gross_profit / wins if wins else 0
            avg_loss = gross_loss / losses if losses else 0
            expectancy = (wins/total * avg_win) - (losses/total * avg_loss) if total else 0
            engine_results.append({
                "multiplier": mult,
                "trades": total,
                "win_rate": win_rate,
                "profit_factor": profit_factor,
                "expectancy": expectancy
            })
        results[engine] = engine_results

    return results, mode_thresholds

# ----------------------------------------------------------------------
# 6. Score Quality Report
# ----------------------------------------------------------------------
def classify_score_quality(discrimination):
    if discrimination["brain_cohens_d"] is None and discrimination["composite_cohens_d"] is None:
        return "Insufficient data"
    brain_d = abs(discrimination["brain_cohens_d"]) if discrimination["brain_cohens_d"] else 0
    comp_d = abs(discrimination["composite_cohens_d"]) if discrimination["composite_cohens_d"] else 0
    avg_d = (brain_d + comp_d) / 2
    if avg_d < 0.2:
        return "Weak"
    elif avg_d < 0.5:
        return "Moderate"
    else:
        return "Strong"

# ----------------------------------------------------------------------
# Report
# ----------------------------------------------------------------------
def print_score_audit_report():
    trades = fetch_trades()
    all_decisions = fetch_all_decisions()
    if not trades:
        print("No closed trades found.")
        return

    print("=" * 70)
    print("  JAGUAR QUANT X – SCORE DISCRIMINATION & PREDICTIVE CALIBRATION AUDIT")
    print("=" * 70)

    # 1. Score Discrimination
    disc = score_discrimination(trades)
    print("\n[1] SCORE DISCRIMINATION")
    print("  Brain Score:")
    if disc["brain_winner"]:
        print(f"    Winners: mean={disc['brain_winner']['mean']:.2f} median={disc['brain_winner']['median']:.2f} range=[{disc['brain_winner']['min']:.1f},{disc['brain_winner']['max']:.1f}]")
        print(f"    Losers:  mean={disc['brain_loser']['mean']:.2f} median={disc['brain_loser']['median']:.2f} range=[{disc['brain_loser']['min']:.1f},{disc['brain_loser']['max']:.1f}]")
        print(f"    Overlap ratio: {disc['brain_overlap']:.2%}")
        if disc["brain_cohens_d"] is not None:
            print(f"    Cohen's d: {disc['brain_cohens_d']:.3f}")
        else:
            print("    Cohen's d: N/A")
    else:
        print("    No data.")
    print("  Composite Score:")
    if disc["composite_winner"]:
        print(f"    Winners: mean={disc['composite_winner']['mean']:.2f} median={disc['composite_winner']['median']:.2f} range=[{disc['composite_winner']['min']:.1f},{disc['composite_winner']['max']:.1f}]")
        print(f"    Losers:  mean={disc['composite_loser']['mean']:.2f} median={disc['composite_loser']['median']:.2f} range=[{disc['composite_loser']['min']:.1f},{disc['composite_loser']['max']:.1f}]")
        print(f"    Overlap ratio: {disc['composite_overlap']:.2%}")
        if disc["composite_cohens_d"] is not None:
            print(f"    Cohen's d: {disc['composite_cohens_d']:.3f}")
        else:
            print("    Cohen's d: N/A")
    else:
        print("    No data.")

    # 2. Engine Contribution Audit (fixed formatting)
    print("\n[2] ENGINE CONTRIBUTION AUDIT")
    audit = engine_contribution_audit(trades)
    contradictions = []
    for name, data in audit.items():
        if data["contradictions"]:
            contradictions.append((name, data["contradictions"]))
        pos_wr_str = f"{data['pos_win_rate']:.1f}%" if data['pos_win_rate'] is not None else "N/A"
        neg_wr_str = f"{data['neg_win_rate']:.1f}%" if data['neg_win_rate'] is not None else "N/A"
        corr_str = f"{data['correlation_win_loss']:.4f}" if isinstance(data['correlation_win_loss'], (int, float)) else str(data['correlation_win_loss'])
        print(f"  {name:25s}  Avg: {data['avg_contribution']:+7.2f}  Pos: {data['pos_count']:5d} (WR={pos_wr_str:>6s})  Neg: {data['neg_count']:5d} (WR={neg_wr_str:>6s})  Zero: {data['zero_count']:5d}  Corr: {corr_str}")
    if contradictions:
        print("\n  ⚠️  Contradictions detected:")
        for eng, issues in contradictions:
            print(f"    {eng}: {', '.join(issues)}")
    else:
        print("  No contradictions found.")

    # 3. Predictive Importance Ranking
    print("\n[3] PREDICTIVE IMPORTANCE RANKING")
    ranking = predictive_importance(trades)
    if ranking:
        print(f"  {'Engine':25s} {'WR Diff':>8s} {'Corr(Win)':>10s} {'Score':>6s}")
        for name, diff, corr, score in ranking:
            corr_str = f"{corr:.4f}" if isinstance(corr, float) else str(corr)
            print(f"  {name:25s} {diff:>+8.2f}% {corr_str:>10s} {score:>6.2f}")
    else:
        print("  No data.")

    # 4. Correlation Analysis
    print("\n[4] CORRELATION ANALYSIS")
    corrs = correlation_analysis(trades)
    for key, val in corrs.items():
        if isinstance(val, float):
            print(f"  {key:25s}: {val:.4f}")
        else:
            print(f"  {key:25s}: {val}")

    # 5. Weight Sensitivity Simulation
    print("\n[5] WEIGHT SENSITIVITY SIMULATION")
    sim_results, thresholds = weight_sensitivity_simulation(all_decisions, trades)
    print(f"  Mode thresholds used: {thresholds}")
    for engine, results in sim_results.items():
        print(f"\n  Engine: {engine}")
        print(f"    {'Multiplier':>10s} {'Trades':>7s} {'Win Rate':>9s} {'PF':>8s} {'Expectancy':>10s}")
        for r in results:
            wr = f"{r['win_rate']:.1f}%" if r['win_rate'] is not None else "N/A"
            pf = f"{r['profit_factor']:.2f}" if r['profit_factor'] is not None else "N/A"
            exp = f"{r['expectancy']:.2f}" if r['expectancy'] is not None else "N/A"
            print(f"    {r['multiplier']:>10.1f} {r['trades']:>7d} {wr:>9s} {pf:>8s} {exp:>10s}")

    # 6. Score Quality
    print("\n[6] SCORE QUALITY CLASSIFICATION")
    quality = classify_score_quality(disc)
    print(f"  Classification: {quality}")
    if quality == "Weak":
        print("  ⚠️  The scoring system lacks predictive power. Consider incorporating additional signal sources or recalibrating weights.")
    elif quality == "Moderate":
        print("  The scoring system provides moderate predictive power. Room for improvement exists.")
    else:
        print("  The scoring system demonstrates strong predictive separation. Good job!")

    # 7. Final Recommendations
    print("\n[7] FINAL RECOMMENDATIONS")
    if quality == "Weak":
        print("  - The current scoring fails to significantly separate winners from losers. Re-examine engine contributions and weightings.")
    if disc["brain_cohens_d"] and abs(disc["brain_cohens_d"]) < 0.2:
        print("  - Brain Score provides negligible differentiation; consider adding new signals or adjusting base contributions.")
    if disc["composite_cohens_d"] and abs(disc["composite_cohens_d"]) < 0.2:
        print("  - Composite Score similarly lacks separation; review the combination of Brain Score with other components.")
    if ranking:
        top_engine = ranking[0][0]
        bottom_engine = ranking[-1][0]
        if ranking[0][1] > 5:
            print(f"  - Engine '{top_engine}' shows meaningful predictive power; consider increasing its weight cautiously.")
        if ranking[-1][1] < -5:
            print(f"  - Engine '{bottom_engine}' negatively correlates with success; consider reducing its weight or removing it.")
    any_trades = any(r["trades"] > 0 for eng_res in sim_results.values() for r in eng_res)
    if not any_trades:
        print("  - Weight simulations indicate that changing engine weights alone may not alter trade selection significantly; the decision threshold is the dominant gate.")
    print("\n" + "=" * 70)
    print("  Audit complete. No changes have been made to the production system.")
