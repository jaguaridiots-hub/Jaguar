# research/brain_logistic.py
import json
import math
import statistics
import copy
from collections import defaultdict
from .database import DB_PATH
import sqlite3

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def fetch_trades_with_contributions(symbol="GC=F", mode="SCALP"):
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

def sigmoid(z):
    if z > 50:
        return 1.0
    if z < -50:
        return 0.0
    return 1.0 / (1.0 + math.exp(-z))

def logistic_regression(X, y, learning_rate=0.01, iterations=5000, lambda_reg=0.0):
    """lambda_reg > 0 enables L2 ridge regularisation."""
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
        # L2 penalty on non-intercept weights
        for j in range(1, n_features + 1):
            gradients[j] += lambda_reg * weights[j]
        for j in range(n_features + 1):
            weights[j] -= learning_rate * gradients[j] / n_samples
    return weights

def calibration_metrics(y_true, y_pred_scores):
    """Return dict with Spearman, Brier, bucket_winrates."""
    if len(y_pred_scores) < 3:
        return {"spearman": None, "brier": None, "bucket_wr": None}
    try:
        spearman = statistics.correlation(y_pred_scores, y_true)
    except:
        spearman = None
    brier = sum((p - a)**2 for p, a in zip(y_pred_scores, y_true)) / len(y_true) if y_true else 0
    # Bucket win rates (5 buckets)
    paired = sorted(zip(y_pred_scores, y_true))
    n = len(paired)
    bucket_wr = {}
    for i in range(0, n, max(1, n//5)):
        chunk = paired[i:i+max(1, n//5)]
        if not chunk:
            continue
        wins = sum(p[1] for p in chunk)
        total = len(chunk)
        bucket_wr[f"bucket{i//max(1,n//5)+1}"] = wins/total*100 if total else 0
    return {"spearman": spearman, "brier": brier, "bucket_wr": bucket_wr}

def exclude_engine_from_X(X, engine_names, exclude_engines):
    """Return a deep copy of X with the specified engine columns zeroed out."""
    X_copy = copy.deepcopy(X)
    for eng in exclude_engines:
        if eng in engine_names:
            idx = engine_names.index(eng)
            for row in X_copy:
                row[idx] = 0
    return X_copy

def run_brain_logistic(symbol="GC=F", mode="SCALP"):
    trades, run_id = fetch_trades_with_contributions(symbol, mode)
    if not trades:
        print("No trades found for training.")
        return

    engine_names, X, y = build_feature_matrix(trades)

    # Model A: all engines
    coefs_full, y_pred_full, met_full = None, None, None
    coefs_full = logistic_regression(X, y)
    if coefs_full:
        y_pred_full = [sigmoid(sum(w * x for w, x in zip(coefs_full, [1.0] + row))) for row in X]
        met_full = calibration_metrics(y, y_pred_full)

    # Model B: without Order Flow
    X_no_of = exclude_engine_from_X(X, engine_names, ["Order Flow"])
    coefs_no_of = logistic_regression(X_no_of, y)
    if coefs_no_of:
        y_pred_noof = [sigmoid(sum(w * x for w, x in zip(coefs_no_of, [1.0] + row))) for row in X_no_of]
        met_noof = calibration_metrics(y, y_pred_noof)

    # Model C: with L2 regularization (lambda=0.1)
    coefs_l2 = logistic_regression(X, y, lambda_reg=0.1)
    if coefs_l2:
        y_pred_l2 = [sigmoid(sum(w * x for w, x in zip(coefs_l2, [1.0] + row))) for row in X]
        met_l2 = calibration_metrics(y, y_pred_l2)

    if coefs_full is None:
        print("Could not train models.")
        return

    print("=" * 70)
    print("  BRAIN LOGISTIC COMPARISON")
    print("=" * 70)
    print(f"  Training campaign : {run_id}  ({len(trades)} trades)")
    print(f"  WARNING: In‑sample evaluation. Validate on unseen campaigns before deploying.")

    # Model comparison table
    models = [
        ("Model A – Full (all engines)", met_full, coefs_full),
        ("Model B – Without Order Flow", met_noof, coefs_no_of),
        ("Model C – L2 Ridge (λ=0.1)", met_l2, coefs_l2),
    ]
    print(f"\n  {'Model':35s} {'Spearman':>9s} {'Brier':>7s} {'Bucket WRs':>20s}")
    print(f"  {'-'*35} {'-'*9} {'-'*7} {'-'*20}")
    for name, met, coefs in models:
        spearman_str = f"{met['spearman']:.4f}" if met and met['spearman'] is not None else "N/A"
        brier_str = f"{met['brier']:.4f}" if met else "N/A"
        bucket_str = " | ".join(f"{v:.1f}%" for v in met['bucket_wr'].values()) if met and met['bucket_wr'] else "N/A"
        print(f"  {name:35s} {spearman_str:>9s} {brier_str:>7s} {bucket_str:>20s}")

    # Recommendation: pick model with best (highest) Spearman
    best_model = max(models, key=lambda m: m[1]['spearman'] if m[1] and m[1]['spearman'] is not None else -1)
    print(f"\n  RECOMMENDED: {best_model[0]} (Spearman = {best_model[1]['spearman']:.4f})")

    # Print learned coefficients for the recommended model
    print(f"\n  LEARNED COEFFICIENTS ({best_model[0]}):")
    print(f"  {'Engine':25s} {'Coefficient':>10s}")
    print(f"  {'-'*25} {'-'*10}")
    intercept = best_model[2][0]
    print(f"  {'(intercept)':25s} {intercept:>+10.4f}")
    for eng, coef in zip(engine_names, best_model[2][1:]):
        print(f"  {eng:25s} {coef:>+10.4f}")

    print("=" * 70)
