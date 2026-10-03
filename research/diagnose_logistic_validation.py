# research/diagnose_logistic_validation.py
import json
import math
import statistics
from collections import defaultdict
from .brain_logistic_validate import (
    fetch_campaign_trades,
    build_feature_matrix,
    sigmoid,
    logistic_regression,
    compute_trade_metrics,
)
from .database import DB_PATH
import sqlite3

def run_diagnose_logistic_validation():
    # ---- 1. Train on GC=F SCALP (without Order Flow) ----
    train_trades, train_run_id = fetch_campaign_trades("GC=F", "SCALP")
    if not train_trades:
        print("❌ No training campaign (GC=F SCALP).")
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

    # Print training coefficients
    print("=" * 70)
    print("  LOGISTIC VALIDATION DIAGNOSTIC")
    print("=" * 70)
    print(f"  Training campaign : {train_run_id}  ({len(train_trades)} trades)")
    print(f"  Model coefficients (intercept + {len(engine_names)} engines):")
    print(f"  {'Engine':25s} {'Coefficient':>10s}")
    for eng, coef in zip(engine_names, coefs[1:]):
        print(f"  {eng:25s} {coef:>+10.6f}")

    # ---- 2. Load validation campaign (BTC-USD SCALP) ----
    val_trades, val_run_id = fetch_campaign_trades("BTC-USD", "SCALP")
    if not val_trades:
        print("❌ No validation campaign (BTC-USD SCALP).")
        return

    # Build features for validation (keep same engine order as training!)
    # We must use the same engine_names list from training to build the validation matrix
    X_val = []
    y_val = []
    for t in val_trades:
        contribs = json.loads(t["contributions_json"]) if t["contributions_json"] else []
        contrib_map = {}
        for eng in contribs:
            name = eng.get("engine") or eng.get("label") or "Unknown"
            contrib_map[name] = eng.get("contribution", 0)
        row = [contrib_map.get(name, 0) for name in engine_names]
        X_val.append(row)
        y_val.append(1 if t["win_loss"] == 1 else 0)

    # Exclude Order Flow in validation as well
    if order_flow_idx is not None:
        for row in X_val:
            row[order_flow_idx] = 0

    # ---- 3. Generate predictions ----
    probs = []
    for row in X_val:
        xi = [1.0] + row
        z = sum(w * x for w, x in zip(coefs, xi))
        prob = sigmoid(z)
        probs.append(prob)

    # ---- 4. Diagnostic statistics ----
    total = len(probs)
    above_50 = sum(1 for p in probs if p >= 0.50)
    above_45 = sum(1 for p in probs if p >= 0.45)
    above_40 = sum(1 for p in probs if p >= 0.40)
    above_30 = sum(1 for p in probs if p >= 0.30)

    min_prob = min(probs)
    max_prob = max(probs)
    mean_prob = statistics.mean(probs)
    median_prob = statistics.median(probs)

    print(f"\n  Validation campaign : {val_run_id}  ({total} trades)")
    print(f"  Predictions generated : {total}")
    print(f"  Predictions >= 0.50   : {above_50}")
    print(f"  Predictions >= 0.45   : {above_45}")
    print(f"  Predictions >= 0.40   : {above_40}")
    print(f"  Predictions >= 0.30   : {above_30}")
    print(f"  Minimum probability   : {min_prob:.6f}")
    print(f"  Maximum probability   : {max_prob:.6f}")
    print(f"  Mean probability      : {mean_prob:.6f}")
    print(f"  Median probability    : {median_prob:.6f}")

    # Check for any NaN values
    nan_count = sum(1 for p in probs if math.isnan(p))
    if nan_count > 0:
        print(f"  ⚠️  NaN predictions   : {nan_count}")

    # Distribution histogram (simple)
    bins = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    print(f"\n  Probability Distribution:")
    for i in range(len(bins)-1):
        lo, hi = bins[i], bins[i+1]
        cnt = sum(1 for p in probs if lo <= p < hi)
        bar = "█" * (cnt * 50 // total) if total else ""
        print(f"  {lo:.1f}-{hi:.1f}: {cnt:>5d} ({cnt/total*100:5.1f}%) {bar}")

    # ---- 5. Conclusion ----
    print(f"\n  DIAGNOSIS:")
    if above_50 == 0:
        print(f"  - No prediction reaches the 0.50 threshold, so no trades are accepted.")
        print(f"  - The model's highest probability is {max_prob:.4f}. Consider lowering the threshold.")
        if max_prob < 0.5:
            print(f"  - The logistic coefficients are pushing all probabilities below 0.5.")
            print(f"  - This indicates the model learned that GC=F SCALP trades are mostly unprofitable")
            print(f"    and applies the same cautious bias to BTC-USD.")
    else:
        print(f"  - Some trades are accepted; the original validation should have shown results.")
        print(f"  - Double-check the threshold logic in run_brain_logistic_validate().")

    print("=" * 70)
