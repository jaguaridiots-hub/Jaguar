# research/score_analysis.py
import sqlite3
import json
import statistics
from .database import DB_PATH

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def _engine_name(eng: dict) -> str:
    return eng.get("engine") or eng.get("label") or "Unknown"

def average_contribution_per_engine():
    conn = get_connection()
    rows = conn.execute("SELECT contributions_json FROM score_log").fetchall()
    conn.close()

    engine_totals = {}
    engine_counts = {}
    for row in rows:
        contribs = json.loads(row["contributions_json"]) if row["contributions_json"] else []
        for eng in contribs:
            name = _engine_name(eng)
            contrib = eng.get("contribution", 0)
            engine_totals[name] = engine_totals.get(name, 0) + contrib
            engine_counts[name] = engine_counts.get(name, 0) + 1

    avg = {name: engine_totals[name]/engine_counts[name] for name in engine_totals}
    return avg

def win_rate_by_engine_sign():
    conn = get_connection()
    rows = conn.execute(
        "SELECT contributions_json, outcome FROM score_log WHERE outcome IN ('WIN','LOSS')"
    ).fetchall()
    conn.close()

    engine_stats = {}
    for row in rows:
        contribs = json.loads(row["contributions_json"]) if row["contributions_json"] else []
        outcome = row["outcome"]
        for eng in contribs:
            name = _engine_name(eng)
            contrib = eng.get("contribution", 0)
            if name not in engine_stats:
                engine_stats[name] = {"pos_wins":0, "pos_total":0, "neg_wins":0, "neg_total":0}
            if contrib > 0:
                engine_stats[name]["pos_total"] += 1
                if outcome == "WIN":
                    engine_stats[name]["pos_wins"] += 1
            elif contrib < 0:
                engine_stats[name]["neg_total"] += 1
                if outcome == "WIN":
                    engine_stats[name]["neg_wins"] += 1

    result = {}
    for eng, stats in engine_stats.items():
        pos_rate = stats["pos_wins"] / stats["pos_total"] if stats["pos_total"] > 0 else None
        neg_rate = stats["neg_wins"] / stats["neg_total"] if stats["neg_total"] > 0 else None
        result[eng] = {
            "positive_win_rate": round(pos_rate*100,2) if pos_rate is not None else "N/A",
            "negative_win_rate": round(neg_rate*100,2) if neg_rate is not None else "N/A"
        }
    return result

def feature_importance_ranking():
    avg = average_contribution_per_engine()
    ranked = sorted(avg.items(), key=lambda x: abs(x[1]), reverse=True)
    return ranked

def correlation_contribution_profitability():
    conn = get_connection()
    rows = conn.execute("""
        SELECT s.contributions_json, t.r_multiple
        FROM score_log s
        JOIN trades t ON s.trade_uuid = t.uuid
        WHERE s.outcome IN ('WIN','LOSS')
    """).fetchall()
    conn.close()

    engine_pairs = {}
    for row in rows:
        contribs = json.loads(row["contributions_json"]) if row["contributions_json"] else []
        r = row["r_multiple"]
        if r is None:
            continue
        for eng in contribs:
            name = _engine_name(eng)
            c = eng.get("contribution", 0)
            engine_pairs.setdefault(name, []).append((c, r))

    correlations = {}
    for name, pairs in engine_pairs.items():
        if len(pairs) < 5:
            correlations[name] = "Insufficient data"
            continue
        xs = [p[0] for p in pairs]
        ys = [p[1] for p in pairs]
        if len(set(xs)) == 1 or len(set(ys)) == 1:
            correlations[name] = "Zero variance"
            continue
        n = len(xs)
        sum_x = sum(xs)
        sum_y = sum(ys)
        sum_xy = sum(x*y for x,y in zip(xs, ys))
        sum_x2 = sum(x*x for x in xs)
        sum_y2 = sum(y*y for y in ys)
        denom = ((n*sum_x2 - sum_x**2)*(n*sum_y2 - sum_y**2))**0.5
        if denom == 0:
            correlations[name] = "N/A"
        else:
            corr = (n*sum_xy - sum_x*sum_y)/denom
            correlations[name] = round(corr, 3)
    return correlations

def score_distributions():
    conn = get_connection()
    brain = [row[0] for row in conn.execute("SELECT brain_score FROM score_log WHERE brain_score IS NOT NULL").fetchall()]
    comp  = [row[0] for row in conn.execute("SELECT composite_score FROM score_log WHERE composite_score IS NOT NULL").fetchall()]
    conn.close()
    return {"brain_scores": brain, "composite_scores": comp}

def print_full_report():
    print("\n" + "="*60)
    print("SCORE CONTRIBUTION ANALYSIS")
    print("="*60)

    print("\n[1] Average Contribution per Engine:")
    avg = average_contribution_per_engine()
    if avg:
        for eng, val in avg.items():
            print(f"  {eng:30s}: {val:+.2f}")
    else:
        print("  No data")

    print("\n[2] Win Rate by Engine Sign (+/-):")
    wr = win_rate_by_engine_sign()
    if wr:
        for eng, rates in wr.items():
            print(f"  {eng:30s}: Pos WR={rates['positive_win_rate']}%  Neg WR={rates['negative_win_rate']}%")
    else:
        print("  No trade outcome data")

    print("\n[3] Feature Importance (by |avg contribution|):")
    fi = feature_importance_ranking()
    if fi:
        for eng, val in fi:
            print(f"  {eng:30s}: {val:+.2f}")
    else:
        print("  No data")

    print("\n[4] Correlation (Contribution vs R‑multiple):")
    corr = correlation_contribution_profitability()
    if corr:
        for eng, val in corr.items():
            print(f"  {eng:30s}: {val}")
    else:
        print("  No data")

    print("\n[5] Brain Score Distribution:")
    dist = score_distributions()
    brain = dist["brain_scores"]
    if brain:
        print(f"  Count: {len(brain)}  Min: {min(brain):.2f}  Max: {max(brain):.2f}  Mean: {statistics.mean(brain):.2f}")
    else:
        print("  No data")

    print("\n[6] Composite Score Distribution:")
    comp = dist["composite_scores"]
    if comp:
        print(f"  Count: {len(comp)}  Min: {min(comp):.2f}  Max: {max(comp):.2f}  Mean: {statistics.mean(comp):.2f}")
    else:
        print("  No data")

    print("="*60)
