# research/decision_quality_audit.py
import json
import math
import statistics
import time
from collections import defaultdict
from .database import DB_PATH
import sqlite3

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def fetch_closed_trades(symbol="GC=F", mode="SCALP"):
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

def sigmoid(z):
    if z > 50: return 1.0
    if z < -50: return 0.0
    return 1.0 / (1.0 + math.exp(-z))

def logistic_regression(X, y, learning_rate=0.01, iterations=5000, lambda_reg=0.0):
    n = len(X)
    if n == 0: return []
    n_features = len(X[0])
    weights = [0.0] * (n_features + 1)
    for _ in range(iterations):
        grads = [0.0] * (n_features + 1)
        for i in range(n):
            xi = [1.0] + X[i]
            z = sum(w * x for w, x in zip(weights, xi))
            pred = sigmoid(z)
            err = pred - y[i]
            for j in range(n_features + 1):
                grads[j] += err * xi[j]
        for j in range(1, n_features + 1):
            grads[j] += lambda_reg * weights[j]
        for j in range(n_features + 1):
            weights[j] -= learning_rate * grads[j] / n
    return weights

def mutual_information(x, y, bins=10):
    n = len(x)
    if n == 0: return 0.0
    min_x, max_x = min(x), max(x)
    if min_x == max_x: return 0.0
    bin_width = (max_x - min_x) / bins
    bin_idx = [min(int((v - min_x) / bin_width), bins-1) for v in x]
    total = n
    p_y1 = sum(y) / total
    p_y0 = 1 - p_y1
    bin_counts = defaultdict(int)
    bin_y1_counts = defaultdict(int)
    for b, yi in zip(bin_idx, y):
        bin_counts[b] += 1
        if yi == 1: bin_y1_counts[b] += 1
    mi = 0.0
    for b in bin_counts:
        p_x = bin_counts[b] / total
        p_y1_given_x = bin_y1_counts.get(b, 0) / bin_counts[b] if bin_counts[b] else 0
        for yi, p_y_given_x in [(1, p_y1_given_x), (0, 1 - p_y1_given_x)]:
            p_y = p_y1 if yi == 1 else p_y0
            if p_y == 0 or p_y_given_x == 0: continue
            p_xy = p_x * p_y_given_x
            mi += p_xy * math.log(p_xy / (p_x * p_y))
    return max(0.0, mi)

def permutation_importance(engine_names, X, y, baseline_acc):
    import random
    random.seed(42)
    importances = {}
    n = len(X)
    if n == 0: return importances
    X_copy = [row[:] for row in X]
    for idx, eng in enumerate(engine_names):
        print(f"    Permutation importance: processing engine {eng} ({idx+1}/{len(engine_names)})", flush=True)
        col = [row[idx] for row in X_copy]
        random.shuffle(col)
        for i, row in enumerate(X_copy):
            row[idx] = col[i]
        coefs = logistic_regression(X_copy, y)
        if not coefs: continue
        correct = 0
        for i in range(n):
            xi = [1.0] + X_copy[i]
            z = sum(w * x for w, x in zip(coefs, xi))
            pred = sigmoid(z) >= 0.5
            if pred == (y[i] == 1): correct += 1
        acc = correct / n * 100
        importances[eng] = baseline_acc - acc
        for i, row in enumerate(X_copy):
            row[idx] = X[i][idx]
    return importances

def run_decision_quality_audit(symbol="GC=F", mode="SCALP"):
    try:
        t0 = time.perf_counter()

        # ---- [1/8] Load trades ----
        print("[1/8] Loading trades...", flush=True)
        trades, run_id = fetch_closed_trades(symbol, mode)
        if not trades:
            print("No closed trades found for the specified symbol/mode.")
            return
        print(f"  Loaded {len(trades)} trades. ({time.perf_counter()-t0:.2f}s)", flush=True)

        # ---- [2/8] Build feature matrix ----
        print("[2/8] Building feature matrix...", flush=True)
        all_contribs = []
        for t in trades:
            contribs = json.loads(t["contributions_json"]) if t["contributions_json"] else []
            all_contribs.append(contribs)

        engine_names = set()
        for clist in all_contribs:
            for eng in clist:
                name = eng.get("engine") or eng.get("label") or "Unknown"
                engine_names.add(name)
        engine_names = sorted(engine_names)

        X = []
        y = []
        for t, clist in zip(trades, all_contribs):
            cmap = {eng.get("engine") or eng.get("label") or "Unknown": eng.get("contribution", 0) for eng in clist}
            row = [cmap.get(name, 0) for name in engine_names]
            X.append(row)
            y.append(1 if t["win_loss"] == 1 else 0)
        print(f"  Feature matrix: {len(X)} rows, {len(engine_names)} columns. ({time.perf_counter()-t0:.2f}s)", flush=True)

        # ---- [3/8] Logistic regression ----
        print("[3/8] Training baseline logistic regression...", flush=True)
        coefs = logistic_regression(X, y)
        if coefs:
            correct = 0
            for i in range(len(X)):
                xi = [1.0] + X[i]
                z = sum(w * x for w, x in zip(coefs, xi))
                pred = sigmoid(z) >= 0.5
                if pred == (y[i] == 1): correct += 1
            baseline_acc = correct / len(X) * 100
        else:
            baseline_acc = 0
        print(f"  Baseline accuracy: {baseline_acc:.1f}% ({time.perf_counter()-t0:.2f}s)", flush=True)

        # ---- [4/8] Mutual information & engine metrics ----
        print("[4/8] Computing mutual information and per-engine statistics...", flush=True)
        engine_metrics = {}
        for idx, eng in enumerate(engine_names):
            col = [row[idx] for row in X]
            winner_vals = [v for v, out in zip(col, y) if out == 1]
            loser_vals  = [v for v, out in zip(col, y) if out == 0]
            mean_win = statistics.mean(winner_vals) if winner_vals else 0
            mean_loss = statistics.mean(loser_vals) if loser_vals else 0
            diff = mean_win - mean_loss
            try:
                corr = statistics.correlation(col, y)
            except:
                corr = 0.0
            mi = mutual_information(col, y)
            engine_metrics[eng] = {
                "mean_win": mean_win,
                "mean_loss": mean_loss,
                "diff": diff,
                "correlation": corr,
                "mi": mi,
            }
        print(f"  Engine metrics complete. ({time.perf_counter()-t0:.2f}s)", flush=True)

        # ---- [5/8] Permutation importance ----
        print("[5/8] Computing permutation importance (this may take a while)...", flush=True)
        perm_imp = permutation_importance(engine_names, X, y, baseline_acc)
        print(f"  Permutation importance done. ({time.perf_counter()-t0:.2f}s)", flush=True)

        # ---- [6/8] Ranking ----
        print("[6/8] Ranking engines...", flush=True)
        combined_score = {}
        for eng in engine_names:
            score = (abs(engine_metrics[eng]["diff"]) * 0.1 +
                     abs(engine_metrics[eng]["correlation"]) * 10 +
                     engine_metrics[eng]["mi"] * 5 +
                     abs(perm_imp.get(eng, 0)) * 0.5)
            combined_score[eng] = score
        ranking = sorted(combined_score.items(), key=lambda x: x[1], reverse=True)
        print(f"  Ranking complete. ({time.perf_counter()-t0:.2f}s)", flush=True)

        # ---- [7/8] Weight / contribution analysis & recommendations ----
        print("[7/8] Analysing weight/contribution...", flush=True)
        mean_abs_contribs = {}
        for eng in engine_names:
            col = [abs(v) for v in [row[engine_names.index(eng)] for row in X]]
            mean_abs_contribs[eng] = statistics.mean(col) if col else 0
        print(f"  Analysis ready. ({time.perf_counter()-t0:.2f}s)", flush=True)

        # ---- [8/8] Report generation ----
        print("[8/8] Generating report...", flush=True)

        total = len(trades)
        wins = sum(y)
        wr = wins / total * 100

        print("=" * 70)
        print("  DECISION QUALITY AUDIT")
        print("=" * 70)
        print(f"  Campaign : {run_id}")
        print(f"  Trades   : {total}  (Wins: {wins}  WinRate: {wr:.1f}%)")
        print(f"  Baseline logistic accuracy : {baseline_acc:.1f}%")

        print("\n  [1] ENGINE CONTRIBUTION COMPARISON")
        print(f"  {'Engine':20s} {'Win μ':>9s} {'Loss μ':>9s} {'Δ μ':>8s} {'Corr':>7s} {'MI':>6s} {'Perm Imp':>8s} {'Importance':>10s}")
        print(f"  {'-'*20} {'-'*9} {'-'*9} {'-'*8} {'-'*7} {'-'*6} {'-'*8} {'-'*10}")
        for eng in engine_names:
            m = engine_metrics[eng]
            perm_val = perm_imp.get(eng, 0)
            imp_score = combined_score[eng]
            print(f"  {eng:20s} {m['mean_win']:>+9.2f} {m['mean_loss']:>+9.2f} {m['diff']:>+8.2f} {m['correlation']:>+7.4f} {m['mi']:>6.4f} {perm_val:>+8.2f}% {imp_score:>10.4f}")

        print("\n  [2] ENGINE RANKING (by predictive importance)")
        for i, (eng, score) in enumerate(ranking, 1):
            print(f"  {i:2d}. {eng:25s}  Score: {score:.4f}")

        print("\n  [3] WEIGHT / CONTRIBUTION ANALYSIS")
        avg_abs = sum(mean_abs_contribs.values()) / max(len(mean_abs_contribs), 1)
        for eng in engine_names:
            abs_c = mean_abs_contribs[eng]
            imp = combined_score[eng]
            if abs_c > avg_abs * 1.5 and imp < combined_score[ranking[len(ranking)//2][0]]:
                print(f"  ⚠️  {eng:25s} is OVERWEIGHTED  (|contrib|={abs_c:.1f}, importance={imp:.4f})")
            elif abs_c < avg_abs * 0.5 and imp > combined_score[ranking[len(ranking)//2][0]]:
                print(f"  💡 {eng:25s} is UNDERWEIGHTED (|contrib|={abs_c:.1f}, importance={imp:.4f})")

        print("\n  [4] RECOMMENDATIONS")
        overweighted = [eng for eng in engine_names if mean_abs_contribs[eng] > avg_abs * 1.5 and combined_score[eng] < combined_score[ranking[len(ranking)//2][0]]]
        underweighted = [eng for eng in engine_names if mean_abs_contribs[eng] < avg_abs * 0.5 and combined_score[eng] > combined_score[ranking[len(ranking)//2][0]]]
        if overweighted:
            print(f"  - Consider reducing weight of: {', '.join(overweighted)}")
        if underweighted:
            print(f"  - Consider increasing weight of: {', '.join(underweighted)}")
        zero_imp = [eng for eng, score in ranking if score < 0.01]
        if zero_imp:
            print(f"  - Engines with negligible predictive value: {', '.join(zero_imp)}  (candidate for disabling)")
        top_engine = ranking[0][0]
        print(f"  - Best single predictor: {top_engine} (consider using it as a threshold gate)")
        print("=" * 70)

        print(f"Total execution time: {time.perf_counter()-t0:.2f}s", flush=True)

    except Exception as e:
        import traceback
        traceback.print_exc()
