# research/brain_optimizer.py
import json
import math
import os
from collections import defaultdict
from datetime import datetime
from .database import DB_PATH
import sqlite3

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def fetch_trades_with_contributions(run_id=None):
    conn = get_connection()
    if run_id:
        query = """
            SELECT t.win_loss, t.pnl, s.brain_score, s.contributions_json, s.regime, s.run_id,
                   t.symbol, t.mode, t.timeframe
            FROM trades t
            JOIN score_log s ON t.uuid = s.trade_uuid
            WHERE t.close_time IS NOT NULL AND s.run_id = ?
        """
        rows = conn.execute(query, (run_id,)).fetchall()
    else:
        query = """
            SELECT t.win_loss, t.pnl, s.brain_score, s.contributions_json, s.regime, s.run_id,
                   t.symbol, t.mode, t.timeframe
            FROM trades t
            JOIN score_log s ON t.uuid = s.trade_uuid
            WHERE t.close_time IS NOT NULL
        """
        rows = conn.execute(query).fetchall()
    conn.close()
    return [dict(r) for r in rows]

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

def compute_importance(engine_names, coefficients):
    results = []
    for idx, name in enumerate(engine_names):
        coef = coefficients[idx + 1]
        results.append((name, coef, abs(coef)))
    results.sort(key=lambda x: x[2], reverse=True)
    return results

def run_brain_optimizer():
    trades = fetch_trades_with_contributions()
    if not trades:
        print("No closed trades found.")
        return

    engine_names, X, y = build_feature_matrix(trades)
    coefs = logistic_regression(X, y, learning_rate=0.01, iterations=5000)
    if not coefs:
        print("Could not fit logistic regression.")
        return

    intercept = coefs[0]
    importance = compute_importance(engine_names, coefs)

    print("=" * 70)
    print("  JAGUAR BRAIN OPTIMIZER – FEATURE IMPORTANCE ANALYSIS")
    print("=" * 70)
    print(f"  Trades analysed : {len(trades)}")
    print(f"  Intercept       : {intercept:+.6f}")
    print()
    print("  Logistic Regression Coefficients (sorted by absolute influence):")
    print(f"  {'Engine':25s} {'Coefficient':>10s} {'Interpretation'}")
    print(f"  {'-'*25} {'-'*10} {'-'*30}")
    for engine, coef, _ in importance:
        direction = "positive" if coef > 0 else "negative"
        print(f"  {engine:25s} {coef:>+10.6f}   {direction} influence")

    threshold = 0.0005
    selected = [(eng, coef) for eng, coef, _ in importance if abs(coef) > threshold]
    print(f"\n  Suggested engines to keep (|coef| > {threshold}):")
    if selected:
        for eng, coef in selected:
            print(f"    {eng} (coef={coef:+.6f})")
    else:
        print("    None meet threshold; all engines have negligible individual impact.")

    print("\n  [1] CORRELATION & MULTICOLLINEARITY WARNING")
    print("  Since many engines have zero or constant contributions, logistic regression")
    print("  may not capture their full effect. Consider removing constant engines.")
    constant_engines = [name for name in engine_names if all(
        row[engine_names.index(name)] == 0 for row in X
    ) or len(set(row[engine_names.index(name)] for row in X)) == 1]
    if constant_engines:
        for eng in constant_engines:
            print(f"    - {eng}")

    print("\n  [2] RECOMMENDED BRAIN ARCHITECTURE (Staged Decision Pipeline)")
    print("  Instead of a flat additive score, use a staged evaluation:")
    print("""
    Stage 1 – Market Context
      • Regime (skip if neutral)
      • Session quality
      • Gann (if active)
    ↓
    Stage 2 – Structural Analysis
      • Structure (BOS / CHOCH)
      • MSS
      • Equal Levels
    ↓
    Stage 3 – Smart Money Confirmation
      • SMC (trend, sweep)
      • Liquidity
      • Order Block
      • FVG
    ↓
    Stage 4 – Entry & Execution Quality
      • Order Flow (delta, pressure)
      • Volume Profile
      • Wyckoff
    ↓
    Stage 5 – Final Probability
      Combine surviving signals using logistic regression weights
      (use only engines that showed predictive value).
    """)
    print("  Each stage can reduce confidence or veto the trade entirely.")
    print("  This prevents a single strong engine from overriding multiple weak signals.")

    print("\n  [3] EXAMPLE USING SELECTED ENGINES")
    example_contribs = {
        "Premium/Discount": -5,
        "Volume Profile": 25,
        "Order Flow": 70,
        "Structure": 15,
        "MSS": 4,
        "Liquidity": -1,
    }
    print(f"    {example_contribs}")
    linear = intercept
    for eng, val in example_contribs.items():
        if eng in engine_names:
            idx = engine_names.index(eng)
            linear += coefs[idx + 1] * val
    prob = sigmoid(linear)
    print(f"    Linear combination : {linear:.4f}")
    print(f"    Predicted win probability : {prob:.4f} ({prob*100:.1f}%)")
    print("  (This is a pure linear model; a staged system would apply additional filters.)")

    print("\n" + "=" * 70)
    print("  This analysis is read-only. No weights or logic were modified.")


# ----------------------------------------------------------------------
# Campaign Comparison
# ----------------------------------------------------------------------
def compare_campaigns():
    all_trades = fetch_trades_with_contributions()
    if not all_trades:
        print("No closed trades found.")
        return

    by_run = defaultdict(list)
    for t in all_trades:
        rid = t.get("run_id")
        if rid is None:
            continue
        by_run[rid].append(t)

    by_symbol_regime = defaultdict(list)
    for t in all_trades:
        regime = t.get("regime") or "UNKNOWN"
        by_symbol_regime[(t["symbol"], regime)].append(t)

    print("=" * 70)
    print("  CAMPAIGN COMPARISON – LOGISTIC REGRESSION COEFFICIENTS")
    print("=" * 70)

    for run_id, trades in sorted(by_run.items()):
        if len(trades) < 50:
            print(f"\n  Run {run_id[:8]}... (only {len(trades)} trades, skipping regression)")
            continue

        engine_names, X, y = build_feature_matrix(trades)
        coefs = logistic_regression(X, y, learning_rate=0.01, iterations=5000)
        if not coefs:
            print(f"\n  Run {run_id[:8]}... regression failed")
            continue

        wins = sum(y)
        total = len(y)
        wr = wins / total * 100
        gross_profit = sum(t["pnl"] for t in trades if t["pnl"] and t["pnl"] > 0)
        gross_loss = abs(sum(t["pnl"] for t in trades if t["pnl"] and t["pnl"] < 0))
        pf = gross_profit / gross_loss if gross_loss else float('inf')
        avg_win = gross_profit / wins if wins else 0
        avg_loss = gross_loss / (total - wins) if (total - wins) else 0
        expectancy = (wins/total * avg_win) - ((total-wins)/total * avg_loss)

        print(f"\n  Run {run_id[:8]}...")
        print(f"  Symbol: {trades[0]['symbol']}  Mode: {trades[0]['mode']}  Regime: {trades[0].get('regime','?')}")
        print(f"  Trades: {total}  WinRate: {wr:.1f}%  PF: {pf:.2f}  Expectancy: {expectancy:.2f}")
        print(f"  Intercept: {coefs[0]:+.6f}")
        importance = compute_importance(engine_names, coefs)
        print(f"  Top 5 coefficients (by |value|):")
        for eng, coef, _ in importance[:5]:
            print(f"    {eng:25s}: {coef:+.6f}")

    print("\n" + "=" * 70)
    print("  REGIME‑SPECIFIC COEFFICIENT COMPARISON")
    print("=" * 70)
    regime_coefs = {}
    for (sym, regime), trades in sorted(by_symbol_regime.items()):
        if len(trades) < 50:
            continue
        engine_names, X, y = build_feature_matrix(trades)
        coefs = logistic_regression(X, y, learning_rate=0.01, iterations=5000)
        if not coefs:
            continue
        importance = compute_importance(engine_names, coefs)
        regime_coefs[(sym, regime)] = {
            'coefs': coefs,
            'engine_names': engine_names,
            'importance': importance,
            'trades': len(trades),
            'win_rate': sum(y)/len(y)*100
        }
        print(f"\n  Symbol: {sym}  Regime: {regime}  Trades: {len(trades)}  WR: {sum(y)/len(y)*100:.1f}%")
        print(f"  Top 5 coefficients:")
        for eng, coef, _ in importance[:5]:
            print(f"    {eng:25s}: {coef:+.6f}")

    all_engines = set()
    for data in regime_coefs.values():
        all_engines.update(data['engine_names'])

    print("\n" + "=" * 70)
    print("  RECOMMENDATION")
    print("=" * 70)
    recommendations = []

    symbols = set()
    for (sym, regime) in regime_coefs:
        symbols.add(sym)

    for sym in symbols:
        sym_keys = [(s, r) for s, r in regime_coefs if s == sym]
        if len(sym_keys) >= 2:
            k1, k2 = sym_keys[0], sym_keys[1]
            coef_diff = 0
            for eng in all_engines:
                idx1 = regime_coefs[k1]['engine_names'].index(eng) if eng in regime_coefs[k1]['engine_names'] else None
                idx2 = regime_coefs[k2]['engine_names'].index(eng) if eng in regime_coefs[k2]['engine_names'] else None
                if idx1 is not None and idx2 is not None:
                    coef_diff += abs(regime_coefs[k1]['coefs'][idx1+1] - regime_coefs[k2]['coefs'][idx2+1])
            if coef_diff > 0.5:
                recommendations.append(
                    f"Significant coefficient differences between {k1[1]} and {k2[1]} for {sym}. "
                    "Separate regime‑specific Brain weight profiles are justified."
                )
            else:
                recommendations.append(
                    f"Coefficient differences between {k1[1]} and {k2[1]} for {sym} are small; "
                    "a single profile may suffice."
                )

    regimes = set()
    for (sym, regime) in regime_coefs:
        regimes.add(regime)

    for reg in regimes:
        reg_keys = [(s, r) for s, r in regime_coefs if r == reg]
        if len(reg_keys) >= 2:
            sym_diff_pairs = []
            for i in range(len(reg_keys)):
                for j in range(i+1, len(reg_keys)):
                    k1, k2 = reg_keys[i], reg_keys[j]
                    coef_diff = 0
                    for eng in all_engines:
                        idx1 = regime_coefs[k1]['engine_names'].index(eng) if eng in regime_coefs[k1]['engine_names'] else None
                        idx2 = regime_coefs[k2]['engine_names'].index(eng) if eng in regime_coefs[k2]['engine_names'] else None
                        if idx1 is not None and idx2 is not None:
                            coef_diff += abs(regime_coefs[k1]['coefs'][idx1+1] - regime_coefs[k2]['coefs'][idx2+1])
                    if coef_diff > 0.5:
                        sym_diff_pairs.append(f"{k1[0]} vs {k2[0]} (regime {reg})")
            if sym_diff_pairs:
                recommendations.append(
                    f"Significant coefficient differences between symbols in regime {reg}: "
                    f"{', '.join(sym_diff_pairs)}. Separate symbol‑specific profiles are justified."
                )

    if not recommendations:
        recommendations.append("Insufficient regime or symbol variation to make a recommendation.")

    for rec in recommendations:
        print(f"  • {rec}")

    print("=" * 70)


# ----------------------------------------------------------------------
# Generate symbol‑ and regime‑specific profiles
# ----------------------------------------------------------------------
PROFILES_DIR = "profiles"
MIN_SAMPLE_SIZE = 500

def generate_profiles():
    all_trades = fetch_trades_with_contributions()
    if not all_trades:
        print("No trades found.")
        return

    by_symbol_regime = defaultdict(list)
    for t in all_trades:
        regime = t.get("regime") or "UNKNOWN"
        by_symbol_regime[(t["symbol"], regime)].append(t)

    print("=" * 70)
    print("  SYMBOL‑AWARE PROFILE GENERATION")
    print("=" * 70)

    generated = 0
    for (symbol, regime), trades in sorted(by_symbol_regime.items()):
        if len(trades) < MIN_SAMPLE_SIZE:
            print(f"  {symbol}/{regime}: only {len(trades)} trades (min {MIN_SAMPLE_SIZE}), skipped.")
            continue

        engine_names, X, y = build_feature_matrix(trades)
        coefs = logistic_regression(X, y, learning_rate=0.01, iterations=5000)
        if not coefs:
            print(f"  {symbol}/{regime}: regression failed.")
            continue

        wins = sum(y)
        total = len(y)
        wr = wins / total * 100
        gross_profit = sum(t["pnl"] for t in trades if t["pnl"] and t["pnl"] > 0)
        gross_loss = abs(sum(t["pnl"] for t in trades if t["pnl"] and t["pnl"] < 0))
        pf = gross_profit / gross_loss if gross_loss else float('inf')
        avg_win = gross_profit / wins if wins else 0
        avg_loss = gross_loss / (total - wins) if (total - wins) else 0
        expectancy = (wins/total * avg_win) - ((total-wins)/total * avg_loss)

        profile = {
            "symbol": symbol,
            "regime": regime,
            "intercept": coefs[0],
            "coefficients": {engine_names[i]: coefs[i+1] for i in range(len(engine_names))},
            "win_rate": wr,
            "profit_factor": pf,
            "expectancy": expectancy,
            "sample_size": total,
            "last_calibration": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        symbol_dir = os.path.join(PROFILES_DIR, symbol)
        os.makedirs(symbol_dir, exist_ok=True)

        profile_path = os.path.join(symbol_dir, f"{regime.lower()}.json")

        should_save = True
        if os.path.exists(profile_path):
            with open(profile_path, 'r') as f:
                old = json.load(f)
            if old.get("win_rate", 0) > wr or old.get("profit_factor", 0) > pf:
                print(f"  {symbol}/{regime}: existing profile has better performance; keeping old.")
                should_save = False

        if should_save:
            with open(profile_path, 'w') as f:
                json.dump(profile, f, indent=2)
            print(f"  {symbol}/{regime}: saved profile ({total} trades, WR={wr:.1f}%, PF={pf:.2f})")
            generated += 1

    if generated == 0:
        print("  No profiles generated (minimum sample size not met or no improvement).")
    else:
        print(f"  Generated/updated {generated} profile(s) in '{PROFILES_DIR}/'.")

    print("=" * 70)


# ----------------------------------------------------------------------
# Profile Validation
# ----------------------------------------------------------------------
def validate_profiles():
    profiles_dir = PROFILES_DIR
    if not os.path.isdir(profiles_dir):
        print(f"No profiles directory found ({profiles_dir}). Run --generate-profiles first.")
        return

    profiles = []
    for symbol in os.listdir(profiles_dir):
        symbol_dir = os.path.join(profiles_dir, symbol)
        if not os.path.isdir(symbol_dir):
            continue
        for file in os.listdir(symbol_dir):
            if file.endswith(".json"):
                regime = file[:-5].upper()
                path = os.path.join(symbol_dir, file)
                with open(path, 'r') as f:
                    profile = json.load(f)
                profile["symbol"] = symbol
                profile["regime"] = regime
                profiles.append(profile)

    if not profiles:
        print("No profiles found.")
        return

    all_trades = fetch_trades_with_contributions()
    by_key = defaultdict(list)
    for t in all_trades:
        regime = t.get("regime") or "UNKNOWN"
        by_key[(t["symbol"], regime)].append(t)

    print("=" * 70)
    print("  PROFILE VALIDATION – SIMULATED PERFORMANCE COMPARISON")
    print("=" * 70)

    for profile in profiles:
        symbol = profile["symbol"]
        regime = profile["regime"]
        key = (symbol, regime)
        trades = by_key.get(key, [])
        if len(trades) < 50:
            print(f"\n  {symbol}/{regime}: insufficient trades ({len(trades)}) – skipped.")
            continue

        engine_names = sorted(profile["coefficients"].keys())
        X = []
        y = []
        for t in trades:
            contribs = json.loads(t["contributions_json"]) if t["contributions_json"] else []
            contrib_map = {eng.get("engine") or eng.get("label") or "Unknown": eng.get("contribution", 0) for eng in contribs}
            row = [contrib_map.get(name, 0) for name in engine_names]
            X.append(row)
            y.append(1 if t["win_loss"] == 1 else 0)

        coefs = [profile["intercept"]] + [profile["coefficients"].get(name, 0) for name in engine_names]

        threshold = 0.55
        simulated_trades = []
        for i in range(len(X)):
            xi = [1.0] + X[i]
            z = sum(w * x for w, x in zip(coefs, xi))
            prob = sigmoid(z)
            if prob >= threshold:
                simulated_trades.append(trades[i])

        if not simulated_trades:
            print(f"\n  {symbol}/{regime}: no trades accepted at threshold {threshold}.")
            continue

        sim_total = len(simulated_trades)
        sim_wins = sum(1 for t in simulated_trades if t["win_loss"] == 1)
        sim_wr = sim_wins / sim_total * 100
        sim_gp = sum(t["pnl"] for t in simulated_trades if t["pnl"] and t["pnl"] > 0)
        sim_gl = abs(sum(t["pnl"] for t in simulated_trades if t["pnl"] and t["pnl"] < 0))
        sim_pf = sim_gp / sim_gl if sim_gl else float('inf')
        sim_avg_win = sim_gp / sim_wins if sim_wins else 0
        sim_avg_loss = sim_gl / (sim_total - sim_wins) if (sim_total - sim_wins) else 0
        sim_expectancy = (sim_wins/sim_total * sim_avg_win) - ((sim_total-sim_wins)/sim_total * sim_avg_loss)

        act_total = len(trades)
        act_wins = sum(y)
        act_wr = act_wins / act_total * 100
        act_gp = sum(t["pnl"] for t in trades if t["pnl"] and t["pnl"] > 0)
        act_gl = abs(sum(t["pnl"] for t in trades if t["pnl"] and t["pnl"] < 0))
        act_pf = act_gp / act_gl if act_gl else float('inf')
        act_avg_win = act_gp / act_wins if act_wins else 0
        act_avg_loss = act_gl / (act_total - act_wins) if (act_total - act_wins) else 0
        act_expectancy = (act_wins/act_total * act_avg_win) - ((act_total-act_wins)/act_total * act_avg_loss)

        print(f"\n  {symbol}/{regime}")
        print(f"  {'Metric':20s} {'Actual (all trades)':>20s} {'Profile (simulated)':>20s} {'Change':>10s}")
        print(f"  {'-'*20} {'-'*20} {'-'*20} {'-'*10}")
        print(f"  {'Trades':20s} {act_total:>20d} {sim_total:>20d} {sim_total - act_total:>+10d}")
        print(f"  {'Win Rate':20s} {act_wr:>19.1f}% {sim_wr:>19.1f}% {sim_wr - act_wr:>+10.1f}%")
        print(f"  {'Profit Factor':20s} {act_pf:>20.2f} {sim_pf:>20.2f} {((sim_pf - act_pf)/act_pf*100) if act_pf else 0:>+10.1f}%")
        print(f"  {'Expectancy':20s} {act_expectancy:>20.2f} {sim_expectancy:>20.2f} {sim_expectancy - act_expectancy:>+10.2f}")

        improved = sim_pf > act_pf and sim_wr > act_wr
        if improved:
            print(f"  ✓ Profile improves both PF and WR. Use this profile.")
        elif sim_pf > act_pf:
            print(f"  ⚠️ Profile improves PF but not WR. Review risk parameters.")
        elif sim_wr > act_wr:
            print(f"  ⚠️ Profile improves WR but not PF. Review entry filtering.")
        else:
            print(f"  ✗ Profile does not improve over default. Keep baseline.")

    print("\n" + "=" * 70)
    print("  Validation complete. Profiles with ✓ are recommended for deployment.")
# ----------------------------------------------------------------------
# Walk-Forward Validation
# ----------------------------------------------------------------------
def fetch_trades_with_open_time():
    """Return all closed trades with open_time, ordered chronologically."""
    conn = get_connection()
    query = """
        SELECT t.win_loss, t.pnl, s.brain_score, s.contributions_json, s.regime, s.run_id,
               t.symbol, t.mode, t.timeframe, t.open_time
        FROM trades t
        JOIN score_log s ON t.uuid = s.trade_uuid
        WHERE t.close_time IS NOT NULL
        ORDER BY t.open_time
    """
    rows = conn.execute(query).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def walk_forward_validation(min_train=500, validation_size=200):
    """True walk-forward validation: train on expanding window, validate on next unseen data."""
    all_trades = fetch_trades_with_open_time()
    if not all_trades:
        print("No trades found.")
        return

    # Group by symbol and regime
    groups = defaultdict(list)
    for t in all_trades:
        regime = t.get("regime") or "UNKNOWN"
        groups[(t["symbol"], regime)].append(t)

    print("=" * 70)
    print("  WALK‑FORWARD VALIDATION – SYMBOL‑AWARE PROFILES")
    print("=" * 70)

    overall_folds = []
    for (symbol, regime), trades in sorted(groups.items()):
        total_trades = len(trades)
        if total_trades < min_train + validation_size:
            print(f"\n  {symbol}/{regime}: only {total_trades} trades (need at least {min_train + validation_size}), skipped.")
            continue

        print(f"\n  {symbol}/{regime} ({total_trades} trades)")

        train_end = min_train  # initial training window size
        fold = 1
        while train_end + validation_size <= total_trades:
            train_trades = trades[:train_end]
            val_trades = trades[train_end:train_end + validation_size]

            # Build model from training set
            engine_names, X_train, y_train = build_feature_matrix(train_trades)
            coefs = logistic_regression(X_train, y_train)
            if not coefs:
                print(f"    Fold {fold}: regression failed for training window.")
                train_end += validation_size
                continue

            # Build profile dict
            profile = {
                "symbol": symbol,
                "regime": regime,
                "intercept": coefs[0],
                "coefficients": {engine_names[i]: coefs[i+1] for i in range(len(engine_names))},
                "sample_size": len(train_trades)
            }

            # Simulate on validation set using profile
            X_val = []
            y_val = []
            for t in val_trades:
                contribs = json.loads(t["contributions_json"]) if t["contributions_json"] else []
                contrib_map = {eng.get("engine") or eng.get("label") or "Unknown": eng.get("contribution", 0) for eng in contribs}
                row = [contrib_map.get(name, 0) for name in engine_names]
                X_val.append(row)
                y_val.append(1 if t["win_loss"] == 1 else 0)

            threshold = 0.55
            simulated = []
            for i in range(len(X_val)):
                xi = [1.0] + X_val[i]
                z = sum(w * x for w, x in zip(coefs, xi))
                prob = sigmoid(z)
                if prob >= threshold:
                    simulated.append(val_trades[i])

            # Metrics for simulated trades
            def calc_metrics(trade_list):
                total = len(trade_list)
                if total == 0:
                    return 0, 0, 0, 0, 0, 0
                wins = sum(1 for t in trade_list if t["win_loss"] == 1)
                wr = wins / total * 100
                gp = sum(t["pnl"] for t in trade_list if t["pnl"] and t["pnl"] > 0)
                gl = abs(sum(t["pnl"] for t in trade_list if t["pnl"] and t["pnl"] < 0))
                pf = gp / gl if gl else float('inf')
                avg_win = gp / wins if wins else 0
                avg_loss = gl / (total - wins) if (total - wins) else 0
                exp = (wins/total * avg_win) - ((total-wins)/total * avg_loss)
                # Max drawdown (simple)
                cumulative = 0
                peak = -float('inf')
                max_dd = 0
                for t in trade_list:
                    cumulative += t["pnl"] or 0
                    if cumulative > peak:
                        peak = cumulative
                    else:
                        dd = peak - cumulative
                        if dd > max_dd:
                            max_dd = dd
                return total, wins, wr, pf, exp, max_dd

            sim_total, sim_wins, sim_wr, sim_pf, sim_exp, sim_dd = calc_metrics(simulated)
            act_total, act_wins, act_wr, act_pf, act_exp, act_dd = calc_metrics(val_trades)

            # Print fold result
            train_period = f"{train_trades[0]['open_time'][:10]} → {train_trades[-1]['open_time'][:10]}"
            val_period   = f"{val_trades[0]['open_time'][:10]} → {val_trades[-1]['open_time'][:10]}"
            print(f"    Fold {fold}:")
            print(f"      Train : {len(train_trades)} trades ({train_period})")
            print(f"      Val   : {len(val_trades)} trades ({val_period})")
            print(f"      Profile (sim)  : Trades {sim_total:4d}  WR {sim_wr:.1f}%  PF {sim_pf:.2f}  Exp {sim_exp:.2f}  DD {sim_dd:.0f}")
            print(f"      Default (all)  : Trades {act_total:4d}  WR {act_wr:.1f}%  PF {act_pf:.2f}  Exp {act_exp:.2f}  DD {act_dd:.0f}")

            overall_folds.append({
                "symbol": symbol,
                "regime": regime,
                "fold": fold,
                "train_period": train_period,
                "val_period": val_period,
                "train_size": len(train_trades),
                "val_size": len(val_trades),
                "profile": {
                    "trades": sim_total,
                    "win_rate": sim_wr,
                    "profit_factor": sim_pf,
                    "expectancy": sim_exp,
                    "max_drawdown": sim_dd
                },
                "default": {
                    "trades": act_total,
                    "win_rate": act_wr,
                    "profit_factor": act_pf,
                    "expectancy": act_exp,
                    "max_drawdown": act_dd
                }
            })

            train_end += validation_size   # expanding window
            fold += 1

    if not overall_folds:
        print("\n  No folds generated. Need more data.")
        return

    # Overall summary
    print("\n" + "=" * 70)
    print("  OVERALL SUMMARY")
    print("=" * 70)
    total_folds = len(overall_folds)
    pf_improvements = []
    wr_improvements = []
    exp_improvements = []
    dd_increases = []
    passes = 0
    for f in overall_folds:
        pf_improvements.append(f["profile"]["profit_factor"] - f["default"]["profit_factor"])
        wr_improvements.append(f["profile"]["win_rate"] - f["default"]["win_rate"])
        exp_improvements.append(f["profile"]["expectancy"] - f["default"]["expectancy"])
        dd_increases.append(f["profile"]["max_drawdown"] - f["default"]["max_drawdown"])
        if f["profile"]["profit_factor"] > f["default"]["profit_factor"] and f["profile"]["win_rate"] > f["default"]["win_rate"]:
            passes += 1

    avg_pf_imp = sum(pf_improvements)/len(pf_improvements)
    avg_wr_imp = sum(wr_improvements)/len(wr_improvements)
    avg_exp_imp = sum(exp_improvements)/len(exp_improvements)
    avg_dd_inc = sum(dd_increases)/len(dd_increases)

    print(f"  Total folds          : {total_folds}")
    print(f"  Folds where profile better : {passes}/{total_folds} ({passes/total_folds*100:.1f}%)")
    print(f"  Avg PF improvement   : {avg_pf_imp:+.2f}")
    print(f"  Avg WR improvement   : {avg_wr_imp:+.2f}%")
    print(f"  Avg Expectancy change: {avg_exp_imp:+.2f}")
    print(f"  Avg Drawdown change  : {avg_dd_inc:+.0f}")
    if passes > total_folds * 0.6 and avg_pf_imp > 0 and avg_dd_inc <= 0:
        print("  ✓ Profile recommended for deployment.")
    else:
        print("  ✗ Profile does not consistently outperform default. Review before deploying.")

    # Save detailed report
    os.makedirs("reports/walk_forward", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = f"reports/walk_forward/report_{timestamp}.json"
    with open(report_path, 'w') as f:
        json.dump({"folds": overall_folds, "summary": {
            "total_folds": total_folds,
            "passes": passes,
            "avg_pf_improvement": avg_pf_imp,
            "avg_wr_improvement": avg_wr_imp,
            "avg_expectancy_change": avg_exp_imp,
            "avg_drawdown_change": avg_dd_inc
        }}, f, indent=2)
    print(f"\n  Detailed report saved to {report_path}")
    print("=" * 70)

def diagnose_walk_forward():
    """Analyse the latest walk-forward report and explain every fold."""
    import glob

    # Find the most recent report
    report_dir = "reports/walk_forward"
    if not os.path.isdir(report_dir):
        print(f"No walk-forward report directory ({report_dir}). Run --walk-forward first.")
        return

    reports = sorted(glob.glob(os.path.join(report_dir, "report_*.json")))
    if not reports:
        print("No walk-forward reports found.")
        return

    latest = reports[-1]
    with open(latest, 'r') as f:
        data = json.load(f)

    folds = data.get("folds", [])
    if not folds:
        print("No folds in report.")
        return

    print("=" * 70)
    print("  WALK‑FORWARD DIAGNOSTICS")
    print("=" * 70)
    print(f"  Report: {latest}")
    print(f"  Total folds: {len(folds)}")

    # Per-fold analysis
    issues = []
    for f in folds:
        sym = f["symbol"]
        regime = f["regime"]
        fold_num = f["fold"]
        train_period = f["train_period"]
        val_period = f["val_period"]
        val_size = f["val_size"]
        prof = f["profile"]
        defa = f["default"]
        rejected = val_size - prof["trades"]
        rejection_pct = (rejected / val_size * 100) if val_size else 0

        # 1. Check time-split: are all dates identical?
        train_start, train_end = train_period.split(" → ")
        val_start, val_end = val_period.split(" → ")
        same_date_train = train_start == train_end
        same_date_val = val_start == val_end
        # 2. Verify chronological order (train_end <= val_start)
        try:
            from datetime import datetime
            train_end_dt = datetime.strptime(train_end.strip(), "%Y-%m-%d")
            val_start_dt = datetime.strptime(val_start.strip(), "%Y-%m-%d")
            proper_order = train_end_dt <= val_start_dt
        except:
            proper_order = None

        # 3. Overfitting check: if profile WR/PF much higher on train (not available, but we can note if profile rejects almost everything)
        # 4. Tiny validation sample
        tiny = val_size < 30
        # 5. Excessive filtering
        excessive_filter = rejection_pct > 80 and prof["trades"] < 30

        # Print fold info
        print(f"\n  Fold {fold_num} – {sym}/{regime}")
        print(f"    Train : {f['train_size']} trades ({train_period})")
        print(f"    Val   : {val_size} trades ({val_period})")
        print(f"    Profile trades : {prof['trades']}  Rejected : {rejected} ({rejection_pct:.1f}%)")
        print(f"    Profile WR : {prof['win_rate']:.1f}%  PF : {prof['profit_factor']:.2f}  Expectancy : {prof['expectancy']:.2f}")
        print(f"    Default WR : {defa['win_rate']:.1f}%  PF : {defa['profit_factor']:.2f}  Expectancy : {defa['expectancy']:.2f}")
        if same_date_train and same_date_val:
            print(f"    ⚠️  All trades on the same date – time‑split is likely meaningless.")
            issues.append((fold_num, "Time-split: all dates identical"))
        elif same_date_train:
            print(f"    ⚠️  Training window is a single date.")
            issues.append((fold_num, "Training window is a single date"))
        elif same_date_val:
            print(f"    ⚠️  Validation window is a single date.")
            issues.append((fold_num, "Validation window is a single date"))
        if proper_order == False:
            print(f"    ⚠️  Validation period begins before training period ends – data leak?")
            issues.append((fold_num, "Validation period overlaps with training"))
        if tiny:
            print(f"    ⚠️  Validation sample < 30 trades – not statistically meaningful.")
            issues.append((fold_num, "Tiny validation sample"))
        if excessive_filter:
            print(f"    ⚠️  Profile is filtering >80% of trades, resulting in very few trades.")
            issues.append((fold_num, "Excessive trade filtering"))

    # Overall verdicts
    print("\n" + "=" * 70)
    print("  VERDICTS")
    print("=" * 70)

    # Data split quality
    has_time_issues = any(("Time-split" in i[1]) or ("single date" in i[1]) for i in issues)
    has_overlap = any("overlap" in i[1].lower() for i in issues)
    split_quality = "PASS" if not (has_time_issues or has_overlap) else "FAIL"
    print(f"  Data split quality         : {split_quality}")
    if split_quality == "FAIL":
        print(f"    → Ensure open_time is a proper timestamp in trades table, not just the date of the campaign run.")

    # Statistical significance
    tiny_folds = sum(1 for i in issues if "Tiny validation" in i[1])
    significance = "PASS" if tiny_folds <= len(folds) * 0.3 else "FAIL"
    print(f"  Statistical significance   : {significance}")
    if significance == "FAIL":
        print(f"    → {tiny_folds} folds have <30 trades. Increase validation window or gather more data.")

    # Generalization
    summary = data.get("summary", {})
    passes = summary.get("passes", 0)
    total = summary.get("total_folds", 0)
    gen_verdict = "PASS" if passes > total * 0.6 else "FAIL"
    print(f"  Generalization             : {gen_verdict} ({passes}/{total} folds improved)")
    if gen_verdict == "FAIL":
        print(f"    → The profile does not consistently beat the default Brain. It may overfit or filter too aggressively.")

    # Deployment readiness
    deploy_ready = (split_quality == "PASS" and significance == "PASS" and gen_verdict == "PASS")
    print(f"  Deployment readiness        : {'PASS' if deploy_ready else 'FAIL'}")
    if not deploy_ready:
        print(f"    Recommendations:")
        if split_quality == "FAIL":
            print(f"    - Fix trade timestamp recording so walk-forward uses real historical dates.")
        if significance == "FAIL":
            print(f"    - Increase data collection before running walk-forward.")
        if gen_verdict == "FAIL":
            print(f"    - Profile may be over-optimistic; consider simpler models or disable aggressive filtering.")

    print("=" * 70)
