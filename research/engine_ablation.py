# research/engine_ablation.py
import json
import math
import statistics
from collections import defaultdict
from .database import DB_PATH
import sqlite3

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def fetch_trades_with_contributions(symbol="GC=F", mode="SCALP"):
    """Fetch closed trades with contributions and outcome for the latest campaign."""
    conn = get_connection()
    row = conn.execute("""
        SELECT run_id FROM research_runs
        WHERE symbols=? AND modes=? AND end_time IS NOT NULL
        ORDER BY start_time DESC LIMIT 1
    """, (symbol, mode)).fetchone()
    if not row:
        return [], None
    run_id = row["run_id"]
    trades = conn.execute("""
        SELECT t.win_loss, t.pnl, s.contributions_json
        FROM trades t
        JOIN score_log s ON t.uuid = s.trade_uuid
        WHERE t.close_time IS NOT NULL AND s.run_id = ?
    """, (run_id,)).fetchall()
    conn.close()
    return [dict(r) for r in trades], run_id

def build_feature_matrix(trades):
    """Build X (list of lists) and y (list of 0/1). Returns engine_names, X, y."""
    engine_names = set()
    for t in trades:
        contribs = json.loads(t["contributions_json"]) if t["contributions_json"] else []
        for eng in contribs:
            name = eng.get("engine") or eng.get("label") or "Unknown"
            engine_names.add(name)
    engine_names = sorted(engine_names)

    X = []
    y = []
    for t in trades:
        contribs = json.loads(t["contributions_json"]) if t["contributions_json"] else []
        contrib_map = {}
        for eng in contribs:
            name = eng.get("engine") or eng.get("label") or "Unknown"
            contrib_map[name] = eng.get("contribution", 0)
        row = [contrib_map.get(name, 0) for name in engine_names]
        X.append(row)
        y.append(1 if t["win_loss"] == 1 else 0)

    return engine_names, X, y

# ---- Logistic model ----
def sigmoid(z):
    if z > 50:
        return 1.0
    if z < -50:
        return 0.0
    return 1.0 / (1.0 + math.exp(-z))

def logistic_regression(X, y, learning_rate=0.01, iterations=5000):
    n_samples = len(X)
    if n_samples == 0:
        return []
    n_features = len(X[0])
    weights = [0.0] * (n_features + 1)
    for _ in range(iterations):
        gradients = [0.0] * (n_features + 1)
        for i in range(n_samples):
            xi = [1.0] + X[i]
            z = sum(w * x for w, x in zip(weights, xi))
            pred = sigmoid(z)
            error = pred - y[i]
            for j in range(n_features + 1):
                gradients[j] += error * xi[j]
        for j in range(n_features + 1):
            weights[j] -= learning_rate * gradients[j] / n_samples
    return weights

# ---- Metrics ----
def compute_calibration_metrics(y_true, y_pred_scores):
    """Calculate Spearman rank correlation, Brier score, and PF by bucket."""
    # Spearman correlation with PnL (using y_true and scores)
    # Actually we only have win_loss, not PnL. For correlation we can use predicted score vs win_loss.
    # We'll compute Spearman between score and win_loss.
    if len(y_pred_scores) < 3:
        return {"spearman": None, "brier": None, "bucket_pf": None}
    # Spearman
    try:
        spearman = statistics.correlation(y_pred_scores, y_true)
    except:
        spearman = None
    # Brier
    brier = sum((p - a)**2 for p, a in zip(y_pred_scores, y_true)) / len(y_true) if y_true else 0
    # PF by bucket (split into 5 buckets by score)
    paired = sorted(zip(y_pred_scores, y_true))
    n = len(paired)
    bucket_pf = {}
    for i in range(0, n, max(1, n//5)):
        chunk = paired[i:i+max(1, n//5)]
        if not chunk:
            continue
        wins = sum(p[1] for p in chunk)
        total = len(chunk)
        bucket_wr = wins/total*100
        # approximate PF: we don't have PnL here, so we'll skip PF per bucket. We can use win_rate as proxy.
        bucket_pf[f"bucket{i//max(1,n//5)+1}"] = bucket_wr
    return {"spearman": spearman, "brier": brier, "bucket_wr": bucket_pf}

# ---- Ablation ----
def run_engine_ablation(symbol="GC=F", mode="SCALP"):
    trades, run_id = fetch_trades_with_contributions(symbol, mode)
    if not trades:
        print("No trades found.")
        return

    engine_names, X, y = build_feature_matrix(trades)
    # Train baseline model on all engines
    coefs = logistic_regression(X, y)
    if not coefs:
        print("Could not train logistic model.")
        return

    # Baseline predictions
    y_pred_base = []
    for row in X:
        xi = [1.0] + row
        z = sum(w * x for w, x in zip(coefs, xi))
        y_pred_base.append(sigmoid(z))

    base_metrics = compute_calibration_metrics(y, y_pred_base)

    print("=" * 70)
    print("  ENGINE ABLATION FRAMEWORK")
    print("=" * 70)
    print(f"  Campaign : {run_id}")
    print(f"  Engines  : {', '.join(engine_names)}")

    print("\n  Baseline model calibration (logistic on all engines):")
    print(f"  Spearman (score vs win) : {base_metrics['spearman']:.4f}" if base_metrics['spearman'] else "  Spearman: N/A")
    print(f"  Brier Score             : {base_metrics['brier']:.4f}")
    # Print bucket win rates
    if base_metrics['bucket_wr']:
        print("  Win Rate by score bucket (baseline):")
        for b, wr in base_metrics['bucket_wr'].items():
            print(f"    {b}: {wr:.1f}%")

    print("\n  Ablation Results (Disable / Invert)")
    print(f"  {'Engine':25s} {'Disabled Spearman':>16s} {'Inverted Spearman':>16s} {'Disabled Brier':>14s} {'Inverted Brier':>14s}")
    print(f"  {'-'*25} {'-'*16} {'-'*16} {'-'*14} {'-'*14}")

    for eng_idx, eng_name in enumerate(engine_names):
        # Disabled: set column to 0
        X_disabled = [[0 if j == eng_idx else val for j, val in enumerate(row)] for row in X]
        y_pred_dis = []
        for row in X_disabled:
            xi = [1.0] + row
            z = sum(w * x for w, x in zip(coefs, xi))
            y_pred_dis.append(sigmoid(z))
        met_dis = compute_calibration_metrics(y, y_pred_dis)

        # Inverted: flip sign
        X_inverted = [[-val if j == eng_idx else val for j, val in enumerate(row)] for row in X]
        y_pred_inv = []
        for row in X_inverted:
            xi = [1.0] + row
            z = sum(w * x for w, x in zip(coefs, xi))
            y_pred_inv.append(sigmoid(z))
        met_inv = compute_calibration_metrics(y, y_pred_inv)

        print(f"  {eng_name:25s} {str(met_dis['spearman'] if met_dis['spearman'] else 'N/A'):>16s} {str(met_inv['spearman'] if met_inv['spearman'] else 'N/A'):>16s} {met_dis['brier']:>14.4f} {met_inv['brier']:>14.4f}")

    print("\n  SUMMARY:")
    print("  Lower Brier = better calibration. Higher Spearman = better ranking.")
    print("  Use this table to decide whether to disable or invert each engine.")
    print("=" * 70)
