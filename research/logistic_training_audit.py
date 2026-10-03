# research/logistic_training_audit.py
import json
import math
import statistics
from collections import defaultdict
from .brain_logistic_validate import (
    fetch_campaign_trades,
    build_feature_matrix,
    logistic_regression,
    sigmoid,
)

def run_logistic_training_audit():
    # ---- Load training data (GC=F SCALP) ----
    train_trades, train_run_id = fetch_campaign_trades("GC=F", "SCALP")
    if not train_trades:
        print("❌ No training campaign (GC=F SCALP).")
        return

    engine_names, X_train, y_train = build_feature_matrix(train_trades)
    n = len(X_train)
    n_wins = sum(y_train)
    n_losses = n - n_wins

    # ---- Print class balance ----
    print("=" * 70)
    print("  LOGISTIC TRAINING AUDIT")
    print("=" * 70)
    print(f"  Training campaign : {train_run_id}")
    print(f"  Total trades      : {n}")
    print(f"  Winners           : {n_wins}  ({n_wins/n*100:.1f}%)")
    print(f"  Losers            : {n_losses}  ({n_losses/n*100:.1f}%)")

    # ---- Feature statistics (raw, no scaling) ----
    print("\n  FEATURE STATISTICS (raw training data)")
    print(f"  {'Engine':25s} {'Mean':>10s} {'Std':>9s} {'Min':>10s} {'Max':>10s}")
    print(f"  {'-'*25} {'-'*10} {'-'*9} {'-'*10} {'-'*10}")
    for idx, eng in enumerate(engine_names):
        col = [row[idx] for row in X_train]
        mean_val = statistics.mean(col)
        stdev_val = statistics.stdev(col) if len(col) >= 2 else 0
        min_val = min(col)
        max_val = max(col)
        print(f"  {eng:25s} {mean_val:>+10.2f} {stdev_val:>9.2f} {min_val:>+10.2f} {max_val:>+10.2f}")

    # ---- Exclude Order Flow (as done in validation) ----
    order_flow_idx = engine_names.index("Order Flow") if "Order Flow" in engine_names else None
    if order_flow_idx is not None:
        for row in X_train:
            row[order_flow_idx] = 0
        # Recompute stats for Order Flow to confirm it's zeroed
        order_flow_col = [row[order_flow_idx] for row in X_train]
        print(f"\n  Order Flow excluded: mean={statistics.mean(order_flow_col):.2f}, std={statistics.stdev(order_flow_col) if len(order_flow_col)>=2 else 0:.2f}")

    # ---- Train logistic regression ----
    coefs = logistic_regression(X_train, y_train)
    if not coefs:
        print("Could not train logistic model.")
        return

    intercept = coefs[0]
    engine_coefs = coefs[1:]

    print(f"\n  TRAINED MODEL")
    print(f"  Intercept          : {intercept:+.6f}")
    print(f"  {'Engine':25s} {'Coefficient':>10s} {'Scaled Coef*':>12s}")
    print(f"  {'-'*25} {'-'*10} {'-'*12}")

    # For each engine, show raw coefficient and also coefficient multiplied by typical feature magnitude
    # (so you can see the actual impact of a typical feature value on the logit)
    for idx, eng in enumerate(engine_names):
        coef = engine_coefs[idx]
        # Typical feature value (mean absolute)
        col = [row[idx] for row in X_train]
        typical_val = statistics.mean([abs(v) for v in col]) if col else 0
        scaled_impact = coef * typical_val
        print(f"  {eng:25s} {coef:>+10.6f} {scaled_impact:>+12.4f}")

    # ---- Compute raw logits (decision function) for training data ----
    logits = []
    for row in X_train:
        xi = [1.0] + row
        z = sum(w * x for w, x in zip(coefs, xi))
        logits.append(z)

    min_logit = min(logits)
    max_logit = max(logits)
    mean_logit = statistics.mean(logits)
    median_logit = statistics.median(logits)

    print(f"\n  RAW LOGIT (z = intercept + Σ coef * feature)")
    print(f"  Minimum     : {min_logit:+.6f}")
    print(f"  Maximum     : {max_logit:+.6f}")
    print(f"  Mean        : {mean_logit:+.6f}")
    print(f"  Median      : {median_logit:+.6f}")

    # Convert logits to probabilities (sigmoid)
    probs = [sigmoid(z) for z in logits]
    print(f"\n  TRAINING PROBABILITIES (sigmoid(logit))")
    print(f"  Minimum     : {min(probs):.6f}")
    print(f"  Maximum     : {max(probs):.6f}")
    print(f"  Mean        : {statistics.mean(probs):.6f}")
    print(f"  Median      : {statistics.median(probs):.6f}")
    above_50 = sum(1 for p in probs if p >= 0.5)
    print(f"  Above 0.50  : {above_50}/{n} ({above_50/n*100:.1f}%)")

    # ---- Root cause analysis ----
    print("\n  ROOT CAUSE ANALYSIS")

    # 1. Check if intercept dominates
    avg_feature_contribution = mean_logit - intercept
    print(f"  Average feature contribution (logit - intercept): {avg_feature_contribution:+.4f}")
    if abs(intercept) > abs(avg_feature_contribution) * 2:
        print(f"  ⚠️  Intercept dominates: the intercept ({intercept:+.4f}) is much larger")
        print(f"      than the average feature contribution ({avg_feature_contribution:+.4f}).")
        print(f"      The model learned a strong prior from the class imbalance.")
        cause = "class imbalance"
    else:
        cause = None

    # 2. Check feature scaling – are features on vastly different scales?
    col_means = []
    for idx in range(len(engine_names)):
        col = [row[idx] for row in X_train]
        col_means.append(statistics.mean([abs(v) for v in col]))
    max_feat = max(col_means)
    min_feat = min(c for c in col_means if c > 0)
    if max_feat / min_feat > 100 and cause is None:
        print(f"  ⚠️  Feature scales vary by >100x (max mean={max_feat:.1f}, min mean={min_feat:.1f}).")
        print(f"      Logistic regression coefficients are sensitive to this.")
        cause = "feature scaling"
    elif max_feat / min_feat > 100:
        print(f"  ⚠️  Feature scales also vary widely (max={max_feat:.1f}, min={min_feat:.1f}),")
        print(f"      which amplifies the class imbalance problem.")
        cause = "class imbalance + feature scaling"

    # 3. Check if max probability is tiny (distribution shift)
    if max(probs) < 0.3:
        print(f"  ⚠️  The highest training probability is only {max(probs):.4f}.")
        print(f"      The model is extremely conservative even on its own training data.")
        if cause is None:
            cause = "class imbalance (severe)"

    # 4. Check regularization – not explicitly used in our logistic_regression (lambda=0)
    print(f"  Regularization strength (lambda) : 0.0 (none)")

    # 5. Distribution shift – check validation probabilities vs training
    # We already know validation max is 0.046; training max is higher (shown above).
    if max(probs) > 0.3 and max(probs) < 0.5:
        print(f"  Training probabilities are below 0.5 despite reasonable max; the model")
        print(f"  doesn't separate winners from losers well even in-sample.")
        if cause is None:
            cause = "weak feature predictiveness"

    if cause is None:
        cause = "multiple factors (class imbalance + weak features + possible distribution shift)"

    print(f"\n  SINGLE MOST LIKELY ROOT CAUSE: {cause}")
    print("=" * 70)
