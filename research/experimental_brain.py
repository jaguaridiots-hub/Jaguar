# research/experimental_brain.py
import json
import math
import statistics
from collections import defaultdict
from .database import DB_PATH
import sqlite3

# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def fetch_production_trades(symbol="GC=F", mode="SCALP"):
    """Fetch closed trades from the latest production campaign for the given symbol/mode."""
    conn = get_connection()
    # Find the latest run_id for a production (non-staged) campaign
    row = conn.execute("""
        SELECT run_id FROM research_runs
        WHERE symbols = ? AND modes = ? AND end_time IS NOT NULL
        ORDER BY start_time DESC LIMIT 1
    """, (symbol, mode)).fetchone()
    if not row:
        return []
    run_id = row["run_id"]
    trades = conn.execute("""
        SELECT t.win_loss, t.pnl, t.r_multiple, s.brain_score, s.contributions_json
        FROM trades t
        JOIN score_log s ON t.uuid = s.trade_uuid
        WHERE t.close_time IS NOT NULL AND s.run_id = ?
    """, (run_id,)).fetchall()
    conn.close()
    return [dict(r) for r in trades], run_id

# ----------------------------------------------------------------------
# Experimental Brain implementation
# ----------------------------------------------------------------------
class ExperimentalStagedBrain:
    """
    Stage 1 – Signal Selection: ignore constant engines.
    Stage 2 – Evidence-Based Scoring: multipliers for predictive engines.
    Stage 3 – Confidence: logistic probability.
    """

    def __init__(self, constant_engines=None, multipliers=None, threshold=0.5):
        self.constant_engines = set(constant_engines or [])
        self.multipliers = multipliers or {
            "Structure": 2.0,
            "MSS": 2.0,
            "Wyckoff": 2.0,
            "Volume Profile": 0.5,
            "Liquidity": 0.5,
        }
        self.threshold = threshold

    def _engine_name(self, eng):
        return eng.get("engine") or eng.get("label") or "Unknown"

    def score(self, contributions):
        """Return a dict with final_score (0-100), confidence, direction."""
        total_contrib = 0.0
        for eng in contributions:
            name = self._engine_name(eng)
            if name in self.constant_engines:
                continue
            contrib = eng.get("contribution", 0)
            mult = self.multipliers.get(name, 1.0)
            total_contrib += contrib * mult

        # Logistic probability
        evidence = total_contrib / 100.0  # scale to avoid extreme z
        prob = 1.0 / (1.0 + math.exp(-evidence * 2.0))  # steepness factor 2
        final_score = prob * 100.0
        direction = "BUY" if evidence > 0 else "SELL"
        return {
            "final_score": round(final_score, 1),
            "confidence": round(prob * 100, 0),
            "direction": direction,
            "evidence": round(evidence, 4)
        }

# ----------------------------------------------------------------------
# Comparison
# ----------------------------------------------------------------------
def run_experimental_brain(symbol="GC=F", mode="SCALP"):
    trades, run_id = fetch_production_trades(symbol, mode)
    if not trades:
        print("No production trades found for comparison.")
        return

    # 1. Determine constant engines from production trades
    all_contribs = []
    for t in trades:
        contribs = json.loads(t["contributions_json"]) if t["contributions_json"] else []
        all_contribs.append(contribs)

    engine_values = defaultdict(list)
    for clist in all_contribs:
        for eng in clist:
            name = eng.get("engine") or eng.get("label") or "Unknown"
            engine_values[name].append(eng.get("contribution", 0))

    constant_engines = []
    for name, vals in engine_values.items():
        if len(set(vals)) == 1:
            constant_engines.append(name)

    # 2. Build experimental brain with those constants ignored
    brain = ExperimentalStagedBrain(constant_engines=constant_engines)

    # 3. Simulate decisions on the same trades
    experimental_results = []
    for t in trades:
        contribs = json.loads(t["contributions_json"]) if t["contributions_json"] else []
        score_info = brain.score(contribs)
        # Decision: if confidence >= threshold and evidence > 0 -> BUY, else REJECT
        decision = "REJECT"
        if score_info["confidence"] >= brain.threshold * 100 and score_info["evidence"] > 0:
            decision = "BUY"
        elif score_info["confidence"] >= brain.threshold * 100 and score_info["evidence"] < 0:
            decision = "SELL"
        experimental_results.append({
            "win_loss": t["win_loss"],
            "pnl": t["pnl"],
            "r_multiple": t["r_multiple"],
            "prod_brain_score": t["brain_score"],
            "exp_score": score_info["final_score"],
            "exp_confidence": score_info["confidence"],
            "exp_decision": decision,
        })

    # 4. Filter trades that would have been taken by experimental brain
    exp_taken = [r for r in experimental_results if r["exp_decision"] in ("BUY", "SELL")]
    prod_taken = [r for r in experimental_results]  # all trades were taken by production? Actually production brain accepted all these trades (they are closed trades). So production trade count = total trades.

    # Metrics for production
    prod_total = len(prod_taken)
    prod_wins = sum(1 for r in prod_taken if r["win_loss"] == 1)
    prod_wr = prod_wins / prod_total * 100 if prod_total else 0
    prod_gp = sum(r["pnl"] for r in prod_taken if r["pnl"] and r["pnl"] > 0)
    prod_gl = abs(sum(r["pnl"] for r in prod_taken if r["pnl"] and r["pnl"] < 0))
    prod_pf = prod_gp / prod_gl if prod_gl else float('inf')
    prod_avg_win = prod_gp / prod_wins if prod_wins else 0
    prod_avg_loss = prod_gl / (prod_total - prod_wins) if (prod_total - prod_wins) else 0
    prod_expectancy = (prod_wins/prod_total * prod_avg_win) - ((prod_total - prod_wins)/prod_total * prod_avg_loss)

    # Metrics for experimental
    exp_total = len(exp_taken)
    exp_wins = sum(1 for r in exp_taken if r["win_loss"] == 1)
    exp_wr = exp_wins / exp_total * 100 if exp_total else 0
    exp_gp = sum(r["pnl"] for r in exp_taken if r["pnl"] and r["pnl"] > 0)
    exp_gl = abs(sum(r["pnl"] for r in exp_taken if r["pnl"] and r["pnl"] < 0))
    exp_pf = exp_gp / exp_gl if exp_gl else float('inf')
    exp_avg_win = exp_gp / exp_wins if exp_wins else 0
    exp_avg_loss = exp_gl / (exp_total - exp_wins) if (exp_total - exp_wins) else 0
    exp_expectancy = (exp_wins/exp_total * exp_avg_win) - ((exp_total - exp_wins)/exp_total * exp_avg_loss)

    # Drawdown for experimental (simple)
    cumulative = 0
    peak = -float('inf')
    max_dd = 0
    for r in exp_taken:
        cumulative += r["pnl"] or 0
        if cumulative > peak:
            peak = cumulative
        else:
            dd = peak - cumulative
            if dd > max_dd:
                max_dd = dd

    # Score discrimination for experimental: brain scores of taken trades
    exp_scores = [r["exp_score"] for r in exp_taken]
    # Compare means
    if exp_total > 0:
        exp_wins_scores = [r["exp_score"] for r in exp_taken if r["win_loss"] == 1]
        exp_losses_scores = [r["exp_score"] for r in exp_taken if r["win_loss"] == 0]
        exp_mean_win = sum(exp_wins_scores)/len(exp_wins_scores) if exp_wins_scores else None
        exp_mean_loss = sum(exp_losses_scores)/len(exp_losses_scores) if exp_losses_scores else None
        # Cohen's d
        if len(exp_wins_scores) >= 2 and len(exp_losses_scores) >= 2:
            pooled_sd = (((len(exp_wins_scores)-1)*statistics.stdev(exp_wins_scores)**2 +
                          (len(exp_losses_scores)-1)*statistics.stdev(exp_losses_scores)**2) /
                         (len(exp_wins_scores)+len(exp_losses_scores)-2))**0.5
            cohens_d = (exp_mean_win - exp_mean_loss)/pooled_sd if pooled_sd else 0
        else:
            cohens_d = None
    else:
        cohens_d = None

    # ---- Print report ----
    print("=" * 70)
    print("  EXPERIMENTAL STAGED BRAIN – COMPARISON")
    print("=" * 70)
    print(f"  Production campaign: {run_id}")
    print(f"  Constant engines removed: {', '.join(constant_engines) if constant_engines else 'none'}")

    print("\n  [1] METRICS COMPARISON")
    print(f"  {'Metric':20s} {'Production Brain':>20s} {'Experimental Brain':>20s}")
    print(f"  {'-'*20} {'-'*20} {'-'*20}")
    print(f"  {'Trades evaluated':20s} {prod_total:>20d} {exp_total:>20d}")
    print(f"  {'Win Rate':20s} {prod_wr:>19.1f}% {exp_wr:>19.1f}%")
    print(f"  {'Profit Factor':20s} {prod_pf:>20.2f} {exp_pf:>20.2f}")
    print(f"  {'Expectancy':20s} {prod_expectancy:>20.2f} {exp_expectancy:>20.2f}")
    if exp_total > 0:
        print(f"  {'Max Drawdown':20s} {'--':>20s} {max_dd:>20.0f}")
    else:
        print(f"  {'Max Drawdown':20s} {'--':>20s} {'N/A':>20s}")

    print("\n  [2] SCORE DISCRIMINATION (Experimental Brain on taken trades)")
    if exp_total > 0 and exp_mean_win is not None:
        print(f"  Mean Winner Score  : {exp_mean_win:.2f}")
        print(f"  Mean Loser Score   : {exp_mean_loss:.2f}")
        if cohens_d is not None:
            print(f"  Cohen's d          : {cohens_d:.3f}")
        else:
            print("  Cohen's d          : N/A")
    else:
        print("  No trades taken by experimental brain.")

    # Sample trades showing differences
    print("\n  [3] SAMPLE TRADE COMPARISONS (first 5)")
    for i, r in enumerate(experimental_results[:5]):
        print(f"  Trade {i+1}:")
        print(f"    Production Brain Score : {r['prod_brain_score']}")
        print(f"    Experimental Score     : {r['exp_score']} (confidence {r['exp_confidence']}%)")
        print(f"    Experimental Decision  : {r['exp_decision']}")
        print(f"    Actual Outcome         : {'WIN' if r['win_loss']==1 else 'LOSS'}")

    print("\n  [4] RECOMMENDATION")
    if exp_pf > prod_pf and exp_wr > prod_wr:
        print("  ✅ Experimental Brain outperforms Production Brain.")
    elif exp_pf > prod_pf:
        print("  ⚠️  Experimental Brain improves Profit Factor but not Win Rate.")
    elif exp_wr > prod_wr:
        print("  ⚠️  Experimental Brain improves Win Rate but not Profit Factor.")
    else:
        print("  ❌ Production Brain currently better. Review engine multipliers.")
    print("=" * 70)
