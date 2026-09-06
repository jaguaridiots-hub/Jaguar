# research/staged_brain_v3.py
import json
import math
import statistics
import os
from collections import defaultdict
from .database import DB_PATH
import sqlite3

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def fetch_campaign_trades(symbol, mode):
    """Return trades and run_id for the latest completed campaign."""
    conn = get_connection()
    row = conn.execute("""
        SELECT run_id FROM research_runs
        WHERE symbols = ? AND modes = ? AND end_time IS NOT NULL
        ORDER BY start_time DESC LIMIT 1
    """, (symbol, mode)).fetchone()
    if not row:
        return [], None
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
# Stage feature extractor (same logic as V2, but without final combination)
# ----------------------------------------------------------------------
class StageFeatures:
    """Compute Trend, Context, Execution probabilities for a single trade."""
    def __init__(self, constant_engines=None):
        self.constant_engines = set(constant_engines or [])

    def _extract_contrib(self, name, contributions):
        for eng in contributions:
            eng_name = eng.get("engine") or eng.get("label") or ""
            if eng_name == name:
                return eng.get("contribution", 0)
        return 0.0

    def trend_prob(self, contributions):
        s = self._extract_contrib("Structure", contributions) * 2.0
        m = self._extract_contrib("MSS", contributions) * 2.0
        evidence = (s + m) / 100.0
        return 1.0 / (1.0 + math.exp(-evidence * 2.5))

    def context_prob(self, contributions):
        w = self._extract_contrib("Wyckoff", contributions) * 2.0
        p = self._extract_contrib("Premium/Discount", contributions)
        f = self._extract_contrib("FVG", contributions)
        evidence = (w + p + f) / 100.0
        return 1.0 / (1.0 + math.exp(-evidence * 2.0))

    def execution_prob(self, contributions):
        o = self._extract_contrib("Order Flow", contributions)
        v = self._extract_contrib("Volume Profile", contributions) * 0.5
        evidence = (o + v) / 100.0
        return 1.0 / (1.0 + math.exp(-evidence * 1.5))

    def features(self, contributions):
        """Return (p_trend, p_context, p_execution)."""
        return (self.trend_prob(contributions),
                self.context_prob(contributions),
                self.execution_prob(contributions))

# ----------------------------------------------------------------------
# Metrics helpers (unchanged from V2)
# ----------------------------------------------------------------------
def brier_score(y_true, y_pred):
    if not y_true:
        return 0
    return sum((p - a)**2 for p, a in zip(y_pred, y_true)) / len(y_true)

def roc_auc_approx(y_true, y_pred):
    pos = [p for p, a in zip(y_pred, y_true) if a == 1]
    neg = [p for p, a in zip(y_pred, y_true) if a == 0]
    if not pos or not neg:
        return None
    total_pairs = len(pos) * len(neg)
    if total_pairs == 0:
        return None
    pos_greater = sum(1 for p in pos for n in neg if p > n)
    ties = sum(1 for p in pos for n in neg if p == n)
    return (pos_greater + 0.5 * ties) / total_pairs

def cohens_d(values1, values2):
    if len(values1) < 2 or len(values2) < 2:
        return None
    pooled_sd = (( (len(values1)-1)*statistics.stdev(values1)**2 +
                   (len(values2)-1)*statistics.stdev(values2)**2 ) /
                 (len(values1)+len(values2)-2))**0.5
    if pooled_sd == 0:
        return 0.0
    return (statistics.mean(values1) - statistics.mean(values2)) / pooled_sd

def compute_trade_metrics(trades):
    if not trades:
        return 0, 0, 0, 0, 0, 0, 0
    total = len(trades)
    wins = sum(1 for t in trades if t["win_loss"] == 1)
    wr = wins / total * 100
    gp = sum(t["pnl"] for t in trades if t["pnl"] and t["pnl"] > 0)
    gl = abs(sum(t["pnl"] for t in trades if t["pnl"] and t["pnl"] < 0))
    pf = gp / gl if gl else float('inf')
    avg_win = gp / wins if wins else 0
    avg_loss = gl / (total - wins) if (total - wins) else 0
    expectancy = (wins/total * avg_win) - ((total-wins)/total * avg_loss)
    cumulative = 0
    peak = -float('inf')
    max_dd = 0
    for t in trades:
        cumulative += t["pnl"] or 0
        if cumulative > peak:
            peak = cumulative
        else:
            dd = peak - cumulative
            if dd > max_dd:
                max_dd = dd
    return total, wins, wr, pf, expectancy, max_dd, None

def calibration_curve(y_true, y_pred, bins=10):
    if not y_true:
        return []
    paired = sorted(zip(y_pred, y_true))
    n = len(paired)
    bin_size = max(1, n // bins)
    curves = []
    for i in range(0, n, bin_size):
        chunk = paired[i:i+bin_size]
        if not chunk:
            continue
        avg_pred = statistics.mean(p[0] for p in chunk)
        win_rate = sum(p[1] for p in chunk) / len(chunk) * 100
        curves.append((avg_pred, win_rate, len(chunk)))
    return curves

# ----------------------------------------------------------------------
# Logistic regression (from brain_optimizer)
# ----------------------------------------------------------------------
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

# ----------------------------------------------------------------------
# Main V3 runner
# ----------------------------------------------------------------------
def run_staged_brain_v3():
    # --- Training data: GC=F SCALP ---
    train_trades, train_run_id = fetch_campaign_trades("GC=F", "SCALP")
    if not train_trades:
        print("No training campaign (GC=F SCALP) found. Run a research campaign first.")
        return

    # Determine constant engines from training set
    engine_values = defaultdict(list)
    for t in train_trades:
        contribs = json.loads(t["contributions_json"]) if t["contributions_json"] else []
        for eng in contribs:
            name = eng.get("engine") or eng.get("label") or "Unknown"
            engine_values[name].append(eng.get("contribution", 0))
    constant_engines = [name for name, vals in engine_values.items() if len(set(vals)) == 1]

    stage = StageFeatures(constant_engines=constant_engines)

    # Build training features and labels
    X_train = []
    y_train = []
    for t in train_trades:
        contribs = json.loads(t["contributions_json"]) if t["contributions_json"] else []
        p1, p2, p3 = stage.features(contribs)
        X_train.append([p1, p2, p3])
        y_train.append(1 if t["win_loss"] == 1 else 0)

    # Train logistic regression
    coefs = logistic_regression(X_train, y_train, learning_rate=0.01, iterations=5000)
    if not coefs:
        print("Logistic regression failed on training data.")
        return
    intercept = coefs[0]
    print("=" * 70)
    print("  STAGED BRAIN V3 – METHODOLOGICALLY SOUND COMPARISON")
    print("=" * 70)
    print(f"  Training campaign : {train_run_id}  ({len(train_trades)} trades)")
    print(f"  Learned coefficients : intercept={intercept:+.4f}, trend={coefs[1]:+.4f}, context={coefs[2]:+.4f}, execution={coefs[3]:+.4f}")

    # Find optimal threshold on training data (maximize profit factor)
    best_thresh = 0.5
    best_pf = 0.0
    for thresh in [i/100 for i in range(40, 80, 2)]:   # search from 0.4 to 0.78
        accepted = []
        for i, t in enumerate(train_trades):
            xi = [1.0] + X_train[i]
            z = sum(w * x for w, x in zip(coefs, xi))
            prob = sigmoid(z)
            if prob >= thresh:
                accepted.append(t)
        if accepted:
            _, _, _, pf, _, _, _ = compute_trade_metrics(accepted)
            if pf > best_pf:
                best_pf = pf
                best_thresh = thresh
    print(f"  Optimal threshold (max PF on training) : {best_thresh:.2f}")

    # --- Validation campaigns ---
    valid_campaigns = [
        ("GC=F", "SWING"),
        ("BTC-USD", "SCALP"),
        ("BTC-USD", "SWING"),
    ]
    print("\n  VALIDATION RESULTS")
    print(f"  {'Campaign':20s} {'Prod PF':>8s} {'V3 PF':>8s} {'Prod WR':>8s} {'V3 WR':>8s} {'Δ PF':>8s} {'Δ WR':>8s} {'V3 Trades':>10s}")
    print(f"  {'-'*20} {'-'*8} {'-'*8} {'-'*8} {'-'*8} {'-'*8} {'-'*8} {'-'*10}")

    all_v3_preds = []
    all_v3_trues = []
    for sym, md in valid_campaigns:
        val_trades, val_run_id = fetch_campaign_trades(sym, md)
        if not val_trades:
            print(f"  {sym+':':6s} {md:6s}   {'N/A':>8s} {'N/A':>8s} (no data)")
            continue

        # Production baseline: all closed trades in this campaign
        prod_total, _, prod_wr, prod_pf, prod_exp, prod_dd, _ = compute_trade_metrics(val_trades)

        # V3 simulation
        X_val = []
        y_val = []
        for t in val_trades:
            contribs = json.loads(t["contributions_json"]) if t["contributions_json"] else []
            p1, p2, p3 = stage.features(contribs)
            X_val.append([p1, p2, p3])
            y_val.append(1 if t["win_loss"] == 1 else 0)

        v3_accepted = []
        v3_y_true = []
        v3_y_pred = []
        for i, t in enumerate(val_trades):
            xi = [1.0] + X_val[i]
            z = sum(w * x for w, x in zip(coefs, xi))
            prob = sigmoid(z)
            if prob >= best_thresh:
                v3_accepted.append(t)
                v3_y_true.append(t["win_loss"])
                v3_y_pred.append(prob)
                all_v3_preds.append(prob)
                all_v3_trues.append(t["win_loss"])

        if v3_accepted:
            _, _, v3_wr, v3_pf, _, _, _ = compute_trade_metrics(v3_accepted)
            pf_change = v3_pf - prod_pf
            wr_change = v3_wr - prod_wr
            print(f"  {sym+':':6s} {md:6s}   {prod_pf:>8.3f} {v3_pf:>8.3f} {prod_wr:>7.1f}% {v3_wr:>7.1f}% {pf_change:>+8.3f} {wr_change:>+8.1f}% {len(v3_accepted):>10d}")
        else:
            print(f"  {sym+':':6s} {md:6s}   {prod_pf:>8.3f} {'N/A':>8s} (no trades accepted)")

    # Overall V3 stats
    if all_v3_preds:
        auc = roc_auc_approx(all_v3_trues, all_v3_preds)
        brier = brier_score(all_v3_trues, all_v3_preds)
        # Cohen's d on validation pooled
        v3_scores_wins = [all_v3_preds[i] for i in range(len(all_v3_preds)) if all_v3_trues[i] == 1]
        v3_scores_losses = [all_v3_preds[i] for i in range(len(all_v3_preds)) if all_v3_trues[i] == 0]
        d = cohens_d(v3_scores_wins, v3_scores_losses) if v3_scores_wins and v3_scores_losses else None
        cal = calibration_curve(all_v3_trues, all_v3_preds)

        print("\n  [2] COMBINED VALIDATION METRICS")
        print(f"  ROC AUC           : {auc:.4f}" if auc else "  ROC AUC : N/A")
        print(f"  Brier Score       : {brier:.4f}")
        print(f"  Cohen's d         : {d:.4f}" if d else "  Cohen's d : N/A")
        print("\n  [3] CALIBRATION CURVE (V3 on validation)")
        if cal:
            print(f"  {'Predicted':>10s} {'Observed WR':>12s} {'Count':>6s}")
            for avg_pred, wr, cnt in cal:
                print(f"  {avg_pred:>10.2f} {wr:>11.1f}% {cnt:>6d}")

    print("\n  [4] RECOMMENDATION")
    if all_v3_preds:
        # Simple heuristic: if V3 outperformed production on at least 2 of 3 validation campaigns
        improved = 0
        total_valid = 0
        for sym, md in valid_campaigns:
            val_trades, _ = fetch_campaign_trades(sym, md)
            if not val_trades:
                continue
            total_valid += 1
            _, _, prod_wr, prod_pf, _, _, _ = compute_trade_metrics(val_trades)
            v3_accepted = []
            for t in val_trades:
                contribs = json.loads(t["contributions_json"]) if t["contributions_json"] else []
                p1, p2, p3 = stage.features(contribs)
                xi = [1.0] + [p1, p2, p3]
                z = sum(w * x for w, x in zip(coefs, xi))
                prob = sigmoid(z)
                if prob >= best_thresh:
                    v3_accepted.append(t)
            if v3_accepted:
                _, _, v3_wr, v3_pf, _, _, _ = compute_trade_metrics(v3_accepted)
                if v3_pf > prod_pf:
                    improved += 1
        if improved >= 2 and total_valid >= 3:
            print("  ✅ V3 consistently outperforms Production on unseen validation. Ready for consideration.")
        else:
            print("  ⚠️  V3 does not yet dominate across all validation campaigns. Refine or gather more data.")
    else:
        print("  No validation trades accepted – unable to draw conclusion.")
    print("=" * 70)
