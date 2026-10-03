# research/engine_variability_audit.py
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
    """Fetch all closed trades with contributions_json and brain_score from score_log."""
    conn = get_connection()
    query = """
        SELECT s.brain_score, s.contributions_json, t.win_loss
        FROM trades t
        JOIN score_log s ON t.uuid = s.trade_uuid
        WHERE t.close_time IS NOT NULL
    """
    rows = conn.execute(query).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def compute_variability_stats(values):
    """Return dict of stats for a list of numeric values."""
    n = len(values)
    if n == 0:
        return {"unique": 0, "min": None, "max": None, "mean": None, "median": None,
                "variance": None, "stdev": None, "repeated_pct": None}
    unique = len(set(values))
    mn = min(values)
    mx = max(values)
    mean_val = statistics.mean(values)
    median_val = statistics.median(values)
    if n >= 2:
        var = statistics.variance(values) if len(set(values)) > 1 else 0.0
        stdev = statistics.stdev(values) if len(set(values)) > 1 else 0.0
    else:
        var = 0.0
        stdev = 0.0
    repeated_pct = ((n - unique) / n * 100) if n > 0 else 0.0
    return {
        "unique": unique,
        "min": mn,
        "max": mx,
        "mean": mean_val,
        "median": median_val,
        "variance": var,
        "stdev": stdev,
        "repeated_pct": repeated_pct
    }

def engine_variability_analysis(trades):
    engine_contribs = defaultdict(list)
    engine_raw_descs = defaultdict(list)
    for t in trades:
        contribs = json.loads(t["contributions_json"]) if t["contributions_json"] else []
        for eng in contribs:
            name = eng.get("engine") or eng.get("label") or "Unknown"
            contrib = eng.get("contribution", 0)
            engine_contribs[name].append(contrib)
            raw_desc = eng.get("raw_desc", None)
            if raw_desc is not None:
                engine_raw_descs[name].append(str(raw_desc))

    report = {}
    for name, contrib_vals in engine_contribs.items():
        stats = compute_variability_stats(contrib_vals)
        raw_unique = len(set(engine_raw_descs.get(name, [])))
        is_static = (stats["unique"] == 1)
        report[name] = {
            "stats": stats,
            "raw_unique": raw_unique,
            "is_static": is_static,
            "sample_count": len(contrib_vals)
        }
    return report

def dynamic_score_index(trades):
    scores = [t["brain_score"] for t in trades if t["brain_score"] is not None]
    if not scores:
        return {"index": None, "classification": "No data"}
    unique = len(set(scores))
    if unique == 1:
        return {"index": 0, "classification": "Broken", "details": "Constant brain score across all trades."}
    if len(scores) < 2:
        return {"index": 0, "classification": "Weak", "details": "Insufficient samples."}
    mean_val = statistics.mean(scores)
    stdev = statistics.stdev(scores)
    cv = stdev / abs(mean_val) if mean_val != 0 else 0
    total = len(scores)
    uniqueness_ratio = unique / total if total > 0 else 0
    if uniqueness_ratio >= 0.5 and cv > 0.3:
        classification = "Excellent"
    elif uniqueness_ratio >= 0.3 or cv > 0.15:
        classification = "Good"
    elif uniqueness_ratio >= 0.1 or cv > 0.05:
        classification = "Moderate"
    elif unique > 1:
        classification = "Weak"
    else:
        classification = "Broken"
    return {
        "index": round(cv, 4),
        "unique_values": unique,
        "total_samples": total,
        "uniqueness_ratio": round(uniqueness_ratio, 4),
        "classification": classification
    }

def print_engine_audit():
    trades = fetch_trades()
    if not trades:
        print("No closed trades found.")
        return

    print("=" * 70)
    print("  JAGUAR QUANT X – ENGINE VARIABILITY AUDIT")
    print("=" * 70)

    report = engine_variability_analysis(trades)
    sorted_engines = sorted(report.items(), key=lambda x: x[1]["stats"]["unique"], reverse=True)

    print("\n[1] ENGINE OUTPUT VARIABILITY")
    print(f"  {'Engine':25s} {'Unique':>6s} {'Min':>8s} {'Max':>8s} {'Mean':>8s} {'Median':>8s} {'StDev':>8s} {'Rep%':>6s} {'Status':>10s}")
    for name, data in sorted_engines:
        s = data["stats"]
        unique = s["unique"]
        mn = f"{s['min']:.1f}" if s['min'] is not None else "N/A"
        mx = f"{s['max']:.1f}" if s['max'] is not None else "N/A"
        mean_val = f"{s['mean']:.1f}" if s['mean'] is not None else "N/A"
        median_val = f"{s['median']:.1f}" if s['median'] is not None else "N/A"
        stdev_val = f"{s['stdev']:.2f}" if s['stdev'] is not None else "N/A"
        rep_pct = f"{s['repeated_pct']:.1f}%"
        status = "STATIC" if data["is_static"] else "Dynamic"
        print(f"  {name:25s} {unique:>6d} {mn:>8s} {mx:>8s} {mean_val:>8s} {median_val:>8s} {stdev_val:>8s} {rep_pct:>6s} {status:>10s}")

    static_engines = [name for name, data in report.items() if data["is_static"]]
    print("\n[2] STATIC ENGINE SUMMARY")
    if static_engines:
        for eng in static_engines:
            data = report[eng]
            s = data["stats"]
            avg_contrib = s["mean"]
            if avg_contrib is not None and abs(avg_contrib) < 0.01 and data["raw_unique"] <= 1:
                note = " (likely by design – neutral signal)"
            else:
                note = " (possible logic defect – constant output)"
            print(f"  • {eng} — constant value {s['min']:.1f}{note}")
    else:
        print("  No static engines found.")

    print("\n[3] VARIABILITY RANKING (most dynamic first)")
    for i, (name, data) in enumerate(sorted_engines, 1):
        s = data["stats"]
        print(f"  {i:2d}. {name:25s}  unique={s['unique']:4d}  stdev={s['stdev'] if s['stdev'] else 0:.2f}  status={'STATIC' if data['is_static'] else 'Dynamic'}")

    dsi = dynamic_score_index(trades)
    print("\n[4] BRAIN ENGINE DYNAMIC SCORE INDEX")
    if dsi["index"] is not None:
        print(f"  CV (stdev/mean): {dsi['index']:.4f}")
        print(f"  Unique Values: {dsi['unique_values']} / {dsi['total_samples']}")
        print(f"  Uniqueness Ratio: {dsi['uniqueness_ratio']:.4f}")
        print(f"  Classification: {dsi['classification']}")
    else:
        print(f"  {dsi.get('details', 'No data')}")

    print("=" * 70)
    print("  Audit complete. No production changes were made.")
