# research/brain_logistic_validate.py
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

# ----------------------------------------------------------------------
# Helpers – identical to brain_logistic.py
# ----------------------------------------------------------------------
def fetch_campaign_trades(symbol, mode):
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
    if z > 50: return 1.0
    if z < -50: return 0.0
    return 1.0 / (1.0 + math.exp(-z))

def logistic_regression(X, y, learning_rate=0.01, iterations=5000, lambda_reg=0.0):
    n_samples = len(X)
    if n_samples == 0: return []
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
        for j in range(1, n_features + 1):
            gradients[j] += lambda_reg * weights[j]
        for j in range(n_features + 1):
            weights[j] -= learning_rate * gradients[j] / n_samples
    return weights

def calibration_metrics(y_true, y_pred_scores):
    if len(y_pred_scores) < 3:
        return {"spearman": None, "brier": None, "bucket_wr": None, "monotonic": None}
    try:
        spearman = statistics.correlation(y_pred_scores, y_true)
    except:
        spearman = None
    brier = sum((p - a)**2 for p, a in zip(y_pred_scores, y_true)) / len(y_true) if y_true else 0
    paired = sorted(zip(y_pred_scores, y_true))
    n = len(paired)
    bucket_wr = {}
    for i in range(0, n, max(1, n//6)):
        chunk = paired[i:i+max(1, n//6)]
        if not chunk: continue
        wins = sum(p[1] for p in chunk)
        total = len(chunk)
        bucket_wr[f"b{i//max(1,n//6)+1}"] = wins/total*100 if total else 0
    wrs = list(bucket_wr.values())
    monotonic = all(wrs[i] <= wrs[i+1] + 5 for i in range(len(wrs)-1))
    return {"spearman": spearman, "brier": brier, "bucket_wr": bucket_wr, "monotonic": monotonic}

def roc_auc_approx(y_true, y_pred):
    pos = [p for p, a in zip(y_pred, y_true) if a == 1]
    neg = [p for p, a in zip(y_pred, y_true) if a == 0]
    if not pos or not neg: return None
    total_pairs = len(pos) * len(neg)
    pos_greater = sum(1 for p in pos for n in neg if p > n)
    ties = sum(1 for p in pos for n in neg if p == n)
    return (pos_greater + 0.5 * ties) / total_pairs

def compute_trade_metrics(trades):
    if not trades: return 0, 0, 0, 0, 0
    total = len(trades)
    wins = sum(1 for t in trades if t["win_loss"]==1)
    wr = wins/total*100
    gp = sum(t["pnl"] for t in trades if t["pnl"] and t["pnl"]>0)
    gl = abs(sum(t["pnl"] for t in trades if t["pnl"] and t["pnl"]<0))
    pf = gp/gl if gl else float('inf')
    avg_win = gp/wins if wins else 0
    avg_loss = gl/(total-wins) if (total-wins) else 0
    exp = (wins/total*avg_win) - ((total-wins)/total*avg_loss)
    return total, wins, wr, pf, exp

# ----------------------------------------------------------------------
# Main validation routine
# ----------------------------------------------------------------------
def run_brain_logistic_validate():
    # ---- 1. Train on GC=F SCALP (without Order Flow) ----
    train_trades, train_run_id = fetch_campaign_trades("GC=F", "SCALP")
    if not train_trades:
        print("❌ No training campaign (GC=F SCALP). Run a research campaign first.")
        return

    engine_names, X_train, y_train = build_feature_matrix(train_trades)
    # Exclude Order Flow
    order_flow_idx = engine_names.index("Order Flow") if "Order Flow" in engine_names else None
    if order_flow_idx is not None:
        for row in X_train:
            row[order_flow_idx] = 0

    coefs = logistic_regression(X_train, y_train)
    if not coefs:
        print("Could not train logistic model.")
        return

    # Compute training predicted probabilities and find best threshold (max PF)
    y_pred_train = []
    for row in X_train:
        xi = [1.0] + row
        z = sum(w*x for w,x in zip(coefs, xi))
        y_pred_train.append(sigmoid(z))

    best_thresh = 0.5
    best_pf = 0
    for thresh in [i/100 for i in range(40, 80, 2)]:
        accepted = [train_trades[i] for i in range(len(train_trades)) if y_pred_train[i] >= thresh]
        if accepted:
            _, _, _, pf, _ = compute_trade_metrics(accepted)
            if pf > best_pf:
                best_pf = pf
                best_thresh = thresh

    # Freeze model
    frozen_model = {
        "engine_names": engine_names,
        "coefs": coefs,
        "threshold": best_thresh,
        "exclude_order_flow": True,
    }

    # ---- 2. Validate on other campaigns ----
    valid_campaigns = [
        ("GC=F", "SWING"),
        ("BTC-USD", "SCALP"),
        ("BTC-USD", "SWING"),
    ]

    print("=" * 70)
    print("  LOGISTIC BRAIN – VALIDATION REPORT")
    print("=" * 70)
    print(f"  Trained on  : {train_run_id}  ({len(train_trades)} trades)")
    print(f"  Threshold   : {best_thresh:.2f} (optimised on training)")
    print(f"  Order Flow  : excluded")
    print()

    overall_pass = True
    for sym, md in valid_campaigns:
        val_trades, val_run_id = fetch_campaign_trades(sym, md)
        if not val_trades:
            print(f"  {sym:10s} {md:6s} : no data – skipped.\n")
            overall_pass = False
            continue

        # Build features
        eng_names, X_val, y_val = build_feature_matrix(val_trades)
        if "Order Flow" in eng_names:
            idx = eng_names.index("Order Flow")
            for row in X_val:
                row[idx] = 0

        # Predict
        y_pred_val = []
        for row in X_val:
            xi = [1.0] + row
            z = sum(w*x for w,x in zip(coefs, xi))
            y_pred_val.append(sigmoid(z))

        # Calibration metrics
        cal = calibration_metrics(y_val, y_pred_val)
        auc = roc_auc_approx(y_val, y_pred_val)

        # Production metrics
        prod_total, _, prod_wr, prod_pf, prod_exp = compute_trade_metrics(val_trades)

        # Logistic Brain metrics (filter by threshold)
        logi_trades = [val_trades[i] for i in range(len(val_trades)) if y_pred_val[i] >= best_thresh]
        logi_total, _, logi_wr, logi_pf, logi_exp = compute_trade_metrics(logi_trades) if logi_trades else (0, 0, 0, 0, 0)

        # Bucket win rates
        bucket_str = " | ".join(f"{v:.1f}%" for v in cal["bucket_wr"].values()) if cal["bucket_wr"] else "N/A"
        spearman_str = f"{cal['spearman']:.4f}" if cal['spearman'] else "N/A"
        brier_str = f"{cal['brier']:.4f}"
        monotonic_str = "YES" if cal.get("monotonic") else "NO"

        # ---- Safe formatting for Logistic Brain metrics ----
        logi_trades_str = f"{logi_total:>15d}" if logi_total else f"{'N/A':>15s}"
        logi_wr_str     = f"{logi_wr:>14.1f}%"   if logi_total else f"{'N/A':>15s}"
        logi_pf_str     = f"{logi_pf:>15.2f}"     if logi_total else f"{'N/A':>15s}"
        logi_exp_str    = f"{logi_exp:>15.2f}"    if logi_total else f"{'N/A':>15s}"

        print(f"  {sym:10s} {md:6s}  ({len(val_trades)} trades)")
        print(f"  {'Metric':20s} {'Full Brain':>15s} {'Logistic Brain':>15s}")
        print(f"  {'-'*20} {'-'*15} {'-'*15}")
        print(f"  {'Spearman':20s} {spearman_str:>15s} {spearman_str:>15s}")
        print(f"  {'Brier':20s} {brier_str:>15s} {brier_str:>15s}")
        print(f"  {'ROC AUC':20s} {f'{auc:.4f}' if auc else 'N/A':>15s} {f'{auc:.4f}' if auc else 'N/A':>15s}")
        print(f"  {'Win Rate':20s} {prod_wr:>14.1f}% {logi_wr_str}")
        print(f"  {'Profit Factor':20s} {prod_pf:>15.2f} {logi_pf_str}")
        print(f"  {'Expectancy':20s} {prod_exp:>15.2f} {logi_exp_str}")
        print(f"  {'Trades':20s} {prod_total:>15d} {logi_trades_str}")
        print(f"  Bucket WRs        : {bucket_str}")
        print(f"  Monotonic?        : {monotonic_str}")

        # Deployment check for this campaign
        passes = (
            cal['spearman'] is not None and cal['spearman'] > 0.05 and
            cal['brier'] < 0.35 and
            cal.get('monotonic') and
            logi_pf > prod_pf and
            logi_total >= 20
        )
        print(f"  DEPLOYMENT CHECK   : {'✅ PASS' if passes else '❌ FAIL'}")
        if not passes:
            overall_pass = False
        print()

    print("=" * 70)
    if overall_pass:
        print("  ✅ Logistic Brain (without Order Flow) meets deployment criteria on all validation campaigns.")
    else:
        print("  ❌ Logistic Brain does NOT meet deployment criteria on all validation campaigns. Review individual results.")
    print("=" * 70)
